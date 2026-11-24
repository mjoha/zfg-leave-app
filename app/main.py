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
from app.models import User
from app.users import DuplicateEmailError, authenticate, create_employee, validate_registration

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
        return RedirectResponse(url="/", status_code=303)
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
    return RedirectResponse(url="/", status_code=303)


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
