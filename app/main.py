from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

APP_NAME = "leave-app"
BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title=APP_NAME, telemetry={"auto_configure": False})
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
def landing(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "index.html",
        {"app_name": APP_NAME},
    )


@app.exception_handler(404)
async def not_found(request: Request, exc: Exception) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "not_found.html",
        {"app_name": APP_NAME},
        status_code=404,
    )
