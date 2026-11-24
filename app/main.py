from datetime import timezone
from pathlib import Path

from fastapi import Depends, FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware

from app.auth import clear_session, establish_session, load_session_user, signed_in_user
from app.config import get_settings
from app.database import get_db
from app.leave import (
    LeaveStateError,
    can_view_leave_request,
    create_leave_request,
    decide_leave_request,
    get_leave_request,
    inclusive_days,
    list_leave_requests_for_user,
    list_pending_reviews,
    status_label,
    validate_decision_comment,
    validate_leave_request,
    withdraw_leave_request,
)
from app.models import ROLE_ADMINISTRATOR, STATUS_APPROVED, STATUS_PENDING, STATUS_REJECTED, User
from app.users import (
    DuplicateEmailError,
    authenticate,
    create_employee,
    role_label,
    validate_display_name,
    validate_registration,
)
from app.validation import ErrorList

BASE_DIR = Path(__file__).resolve().parent


def _template_defaults(request: Request) -> dict[str, object]:
    return {"app_name": get_settings().app_name, "current_user": signed_in_user(request)}


app = FastAPI(title=get_settings().app_name, telemetry={"auto_configure": False})
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates", context_processors=[_template_defaults])


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
def landing(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "index.html", {})


def _register_context(errors: list[str], email: str, display_name: str) -> dict[str, object]:
    return {
        "errors": errors,
        "email": email.strip(),
        "display_name": display_name.strip(),
    }


@app.get("/register", response_class=HTMLResponse)
def register_form(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "register.html",
        _register_context([], "", ""),
    )


@app.post("/register")
def register_submit(
    request: Request,
    email: str = Form(""),
    display_name: str = Form(""),
    password: str = Form(""),
    password_confirm: str = Form(""),
    db: Session = Depends(get_db),
) -> Response:
    data, errors = validate_registration(email, display_name, password, password_confirm)
    if data is None:
        return templates.TemplateResponse(
            request,
            "register.html",
            _register_context(errors, email, display_name),
            status_code=400,
        )
    try:
        create_employee(db, data)
    except DuplicateEmailError:
        return templates.TemplateResponse(
            request,
            "register.html",
            _register_context(["An account with that email already exists."], email, display_name),
            status_code=400,
        )
    except OperationalError:
        db.rollback()
        return templates.TemplateResponse(
            request,
            "database_unavailable.html",
            {},
            status_code=503,
        )
    return RedirectResponse(url="/account-created", status_code=303)


def _login_context(errors: list[str], email: str) -> dict[str, object]:
    return {"errors": errors, "email": email.strip()}


@app.get("/login", response_class=HTMLResponse)
def login_form(request: Request) -> Response:
    if request.session.get("user_id") is not None:
        return RedirectResponse(url="/profile", status_code=303)
    return templates.TemplateResponse(request, "login.html", _login_context([], ""))


@app.post("/login")
def login_submit(
    request: Request,
    email: str = Form(""),
    password: str = Form(""),
    db: Session = Depends(get_db),
) -> Response:
    errors = ErrorList()
    if not email.strip() or not password:
        errors.add("Enter your email and password.")
    if errors:
        return templates.TemplateResponse(
            request,
            "login.html",
            _login_context(errors.messages(), email),
            status_code=400,
        )
    try:
        user = authenticate(db, email, password)
    except OperationalError:
        db.rollback()
        return templates.TemplateResponse(
            request,
            "database_unavailable.html",
            {},
            status_code=503,
        )
    if user is None:
        return templates.TemplateResponse(
            request,
            "login.html",
            _login_context(["Email or password is incorrect."], email),
            status_code=400,
        )
    establish_session(request, user.id)
    return RedirectResponse(url="/profile", status_code=303)


def _format_timestamp(value) -> str:
    if value.tzinfo is None:
        return value.strftime("%Y-%m-%d %H:%M")
    return value.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def _profile_context(user: User, errors: list[str], display_name: str, *, saved: bool) -> dict[str, object]:
    return {
        "profile_email": user.email,
        "profile_role": role_label(user.role),
        "profile_created": _format_timestamp(user.created_at),
        "saved_display_name": user.display_name,
        "display_name": display_name,
        "errors": errors,
        "saved": saved,
    }


@app.get("/profile", response_class=HTMLResponse)
def profile_page(request: Request, db: Session = Depends(get_db)) -> Response:
    try:
        user = load_session_user(request, db)
    except OperationalError:
        db.rollback()
        return templates.TemplateResponse(request, "database_unavailable.html", {}, status_code=503)
    if user is None:
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse(
        request,
        "profile.html",
        _profile_context(user, [], user.display_name, saved=request.query_params.get("saved") == "1"),
    )


@app.post("/profile")
def profile_update(
    request: Request,
    display_name: str = Form(""),
    db: Session = Depends(get_db),
) -> Response:
    try:
        user = load_session_user(request, db)
    except OperationalError:
        db.rollback()
        return templates.TemplateResponse(request, "database_unavailable.html", {}, status_code=503)
    if user is None:
        return RedirectResponse(url="/login", status_code=303)
    cleaned, errors = validate_display_name(display_name)
    if cleaned is None:
        return templates.TemplateResponse(
            request,
            "profile.html",
            _profile_context(user, errors, display_name.strip(), saved=False),
            status_code=400,
        )
    user.display_name = cleaned
    db.commit()
    return RedirectResponse(url="/profile?saved=1", status_code=303)


def _request_form_context(errors: list[str], start_date: str, end_date: str, reason: str) -> dict[str, object]:
    return {
        "errors": errors,
        "start_date": start_date,
        "end_date": end_date,
        "reason": reason,
    }


@app.get("/requests/new", response_class=HTMLResponse)
def new_leave_request(request: Request, db: Session = Depends(get_db)) -> Response:
    try:
        user = load_session_user(request, db)
    except OperationalError:
        db.rollback()
        return templates.TemplateResponse(request, "database_unavailable.html", {}, status_code=503)
    if user is None:
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse(request, "request_form.html", _request_form_context([], "", "", ""))


@app.post("/requests")
def submit_leave_request(
    request: Request,
    start_date: str = Form(""),
    end_date: str = Form(""),
    reason: str = Form(""),
    db: Session = Depends(get_db),
) -> Response:
    try:
        user = load_session_user(request, db)
    except OperationalError:
        db.rollback()
        return templates.TemplateResponse(request, "database_unavailable.html", {}, status_code=503)
    if user is None:
        return RedirectResponse(url="/login", status_code=303)
    data, errors = validate_leave_request(start_date, end_date, reason)
    if data is None:
        return templates.TemplateResponse(
            request,
            "request_form.html",
            _request_form_context(errors, start_date, end_date, reason),
            status_code=400,
        )
    try:
        create_leave_request(db, user.id, data)
    except LeaveStateError as exc:
        return templates.TemplateResponse(
            request,
            "request_form.html",
            _request_form_context([exc.message], start_date, end_date, reason),
            status_code=400,
        )
    except OperationalError:
        db.rollback()
        return templates.TemplateResponse(request, "database_unavailable.html", {}, status_code=503)
    return RedirectResponse(url="/requests?saved=1", status_code=303)


def _request_rows(rows: list) -> list[dict[str, object]]:
    return [
        {
            "id": row.id,
            "start_date": row.start_date.isoformat(),
            "end_date": row.end_date.isoformat(),
            "day_count": inclusive_days(row.start_date, row.end_date),
            "reason": row.reason,
            "status_label": status_label(row.status),
        }
        for row in rows
    ]


def _detail_context(
    row,
    user: User,
    errors: list[str],
    *,
    withdrawn: bool,
    decided: bool = False,
    comment: str = "",
) -> dict[str, object]:
    return {
        "item": {
            "id": row.id,
            "start_date": row.start_date.isoformat(),
            "end_date": row.end_date.isoformat(),
            "day_count": inclusive_days(row.start_date, row.end_date),
            "reason": row.reason,
            "status_label": status_label(row.status),
            "created": _format_timestamp(row.created_at),
            "decision_comment": row.decision_comment,
            "can_withdraw": row.status == STATUS_PENDING and row.user_id == user.id,
            "can_decide": row.status == STATUS_PENDING and user.role == ROLE_ADMINISTRATOR,
        },
        "errors": errors,
        "withdrawn": withdrawn,
        "decided": decided,
        "comment": comment,
    }


@app.get("/requests/{request_id}", response_class=HTMLResponse)
def leave_request_detail(request: Request, request_id: int, db: Session = Depends(get_db)) -> Response:
    try:
        user = load_session_user(request, db)
        row = get_leave_request(db, request_id) if user is not None else None
    except OperationalError:
        db.rollback()
        return templates.TemplateResponse(request, "database_unavailable.html", {}, status_code=503)
    if user is None:
        return RedirectResponse(url="/login", status_code=303)
    if row is None or not can_view_leave_request(user, row):
        return templates.TemplateResponse(request, "not_found.html", {}, status_code=404)
    return templates.TemplateResponse(
        request,
        "request_detail.html",
        _detail_context(
            row,
            user,
            [],
            withdrawn=request.query_params.get("withdrawn") == "1",
            decided=request.query_params.get("decided") in {STATUS_APPROVED, STATUS_REJECTED},
        ),
    )


def _decide(request: Request, request_id: int, db: Session, status: str, comment_raw: str) -> Response:
    try:
        user = load_session_user(request, db)
        row = get_leave_request(db, request_id) if user is not None else None
    except OperationalError:
        db.rollback()
        return templates.TemplateResponse(request, "database_unavailable.html", {}, status_code=503)
    if user is None:
        return RedirectResponse(url="/login", status_code=303)
    if row is None or not can_view_leave_request(user, row):
        return templates.TemplateResponse(request, "not_found.html", {}, status_code=404)
    if user.role != ROLE_ADMINISTRATOR:
        return templates.TemplateResponse(request, "forbidden.html", {}, status_code=403)
    comment, comment_errors = validate_decision_comment(comment_raw)
    if comment_errors:
        return templates.TemplateResponse(
            request,
            "request_detail.html",
            _detail_context(row, user, comment_errors, withdrawn=False, comment=comment_raw),
            status_code=400,
        )
    try:
        decide_leave_request(db, row, status, comment)
    except LeaveStateError as exc:
        return templates.TemplateResponse(
            request,
            "request_detail.html",
            _detail_context(row, user, [exc.message], withdrawn=False, comment=comment_raw),
            status_code=400,
        )
    except OperationalError:
        db.rollback()
        return templates.TemplateResponse(request, "database_unavailable.html", {}, status_code=503)
    return RedirectResponse(url=f"/requests/{row.id}?decided={status}", status_code=303)


@app.post("/requests/{request_id}/approve")
def approve_request(
    request: Request,
    request_id: int,
    comment: str = Form(""),
    db: Session = Depends(get_db),
) -> Response:
    return _decide(request, request_id, db, STATUS_APPROVED, comment)


@app.post("/requests/{request_id}/reject")
def reject_request(
    request: Request,
    request_id: int,
    comment: str = Form(""),
    db: Session = Depends(get_db),
) -> Response:
    return _decide(request, request_id, db, STATUS_REJECTED, comment)


def _review_rows(rows: list[tuple]) -> list[dict[str, object]]:
    return [
        {
            "id": row.id,
            "employee": employee_name,
            "start_date": row.start_date.isoformat(),
            "end_date": row.end_date.isoformat(),
            "reason": row.reason,
            "status_label": status_label(row.status),
        }
        for row, employee_name in rows
    ]


@app.get("/reviews", response_class=HTMLResponse)
def review_queue(request: Request, db: Session = Depends(get_db)) -> Response:
    try:
        user = load_session_user(request, db)
        rows = list_pending_reviews(db) if user is not None and user.role == ROLE_ADMINISTRATOR else []
    except OperationalError:
        db.rollback()
        return templates.TemplateResponse(request, "database_unavailable.html", {}, status_code=503)
    if user is None:
        return RedirectResponse(url="/login", status_code=303)
    if user.role != ROLE_ADMINISTRATOR:
        return templates.TemplateResponse(request, "forbidden.html", {}, status_code=403)
    return templates.TemplateResponse(request, "review_queue.html", {"reviews": _review_rows(rows)})


@app.post("/requests/{request_id}/withdraw")
def withdraw_request(request: Request, request_id: int, db: Session = Depends(get_db)) -> Response:
    try:
        user = load_session_user(request, db)
        row = get_leave_request(db, request_id) if user is not None else None
    except OperationalError:
        db.rollback()
        return templates.TemplateResponse(request, "database_unavailable.html", {}, status_code=503)
    if user is None:
        return RedirectResponse(url="/login", status_code=303)
    if row is None or row.user_id != user.id:
        return templates.TemplateResponse(request, "not_found.html", {}, status_code=404)
    try:
        withdraw_leave_request(db, row)
    except LeaveStateError as exc:
        return templates.TemplateResponse(
            request,
            "request_detail.html",
            _detail_context(row, user, [exc.message], withdrawn=False),
            status_code=400,
        )
    except OperationalError:
        db.rollback()
        return templates.TemplateResponse(request, "database_unavailable.html", {}, status_code=503)
    return RedirectResponse(url=f"/requests/{row.id}?withdrawn=1", status_code=303)


@app.get("/requests", response_class=HTMLResponse)
def my_leave_requests(request: Request, db: Session = Depends(get_db)) -> Response:
    try:
        user = load_session_user(request, db)
        rows = list_leave_requests_for_user(db, user.id) if user is not None else []
    except OperationalError:
        db.rollback()
        return templates.TemplateResponse(request, "database_unavailable.html", {}, status_code=503)
    if user is None:
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse(
        request,
        "request_list.html",
        {
            "requests": _request_rows(rows),
            "saved": request.query_params.get("saved") == "1",
        },
    )


@app.post("/logout")
def logout(request: Request) -> Response:
    clear_session(request)
    return RedirectResponse(url="/", status_code=303)


@app.get("/account-created", response_class=HTMLResponse)
def account_created(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "account_created.html", {})


@app.exception_handler(404)
async def not_found(request: Request, exc: Exception) -> HTMLResponse:
    return templates.TemplateResponse(request, "not_found.html", {}, status_code=404)


_session_settings = get_settings()
app.add_middleware(
    SessionMiddleware,
    secret_key=_session_settings.session_secret,
    session_cookie="leave_session",
    max_age=_session_settings.session_max_age,
    same_site="lax",
    https_only=_session_settings.session_https_only,
)
