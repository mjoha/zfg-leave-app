from datetime import date, timezone
from pathlib import Path

from fastapi import Depends, FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware

from app.config import get_settings
from app.database import get_db, get_engine
from app.leave import create_leave_request, inclusive_days, validate_leave_request
from app.models import User
from app.users import (
    DuplicateEmailError,
    authenticate,
    create_employee,
    role_label,
    validate_display_name,
    validate_registration,
)

BASE_DIR = Path(__file__).resolve().parent


def signed_in_user(request: Request) -> User | None:
    user_id = request.session.get("user_id")
    if not isinstance(user_id, int):
        return None
    db = Session(get_engine())
    try:
        user = db.get(User, user_id)
        if user is None:
            request.session.pop("user_id", None)
            return None
        db.expunge(user)
        return user
    except OperationalError:
        return None
    finally:
        db.close()


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
    if not email.strip() or not password:
        return templates.TemplateResponse(
            request,
            "login.html",
            _login_context(["Enter your email and password."], email),
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
    request.session.clear()
    request.session["user_id"] = user.id
    return RedirectResponse(url="/profile", status_code=303)


def _profile_user(request: Request, db: Session) -> User | None:
    user_id = request.session.get("user_id")
    if not isinstance(user_id, int):
        return None
    user = db.get(User, user_id)
    if user is None:
        request.session.pop("user_id", None)
    return user


def _format_created(user: User) -> str:
    created = user.created_at
    if created.tzinfo is None:
        return created.strftime("%Y-%m-%d %H:%M")
    return created.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def _profile_context(user: User, errors: list[str], display_name: str, *, saved: bool) -> dict[str, object]:
    return {
        "profile_email": user.email,
        "profile_role": role_label(user.role),
        "profile_created": _format_created(user),
        "saved_display_name": user.display_name,
        "display_name": display_name,
        "errors": errors,
        "saved": saved,
    }


@app.get("/profile", response_class=HTMLResponse)
def profile_page(request: Request, db: Session = Depends(get_db)) -> Response:
    try:
        user = _profile_user(request, db)
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
        user = _profile_user(request, db)
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
        user = _profile_user(request, db)
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
        user = _profile_user(request, db)
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
    except OperationalError:
        db.rollback()
        return templates.TemplateResponse(request, "database_unavailable.html", {}, status_code=503)
    return RedirectResponse(
        url=f"/requests/created?start={data.start_date.isoformat()}&end={data.end_date.isoformat()}",
        status_code=303,
    )


@app.get("/requests/created", response_class=HTMLResponse)
def leave_request_created(request: Request, db: Session = Depends(get_db)) -> Response:
    try:
        user = _profile_user(request, db)
    except OperationalError:
        db.rollback()
        return templates.TemplateResponse(request, "database_unavailable.html", {}, status_code=503)
    if user is None:
        return RedirectResponse(url="/login", status_code=303)
    start_raw = request.query_params.get("start", "")
    end_raw = request.query_params.get("end", "")
    try:
        start_date = date.fromisoformat(start_raw)
        end_date = date.fromisoformat(end_raw)
    except ValueError:
        start_date = None
        end_date = None
    day_count = inclusive_days(start_date, end_date) if start_date and end_date and end_date >= start_date else None
    return templates.TemplateResponse(
        request,
        "request_created.html",
        {"start_date": start_raw, "end_date": end_raw, "day_count": day_count},
    )


@app.post("/logout")
def logout(request: Request) -> Response:
    request.session.clear()
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
