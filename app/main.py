from pathlib import Path

from fastapi import Depends, FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.users import DuplicateEmailError, create_employee, validate_registration

BASE_DIR = Path(__file__).resolve().parent


def _template_defaults(request: Request) -> dict[str, object]:
    return {"app_name": get_settings().app_name}


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


@app.get("/account-created", response_class=HTMLResponse)
def account_created(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "account_created.html", {})


@app.exception_handler(404)
async def not_found(request: Request, exc: Exception) -> HTMLResponse:
    return templates.TemplateResponse(request, "not_found.html", {}, status_code=404)
