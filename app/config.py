import os
import secrets
from dataclasses import dataclass
from pathlib import Path

DEFAULT_APP_NAME = "leave-app"
DEFAULT_DATABASE_URL = "sqlite:///./data/leave.db"
DEFAULT_DATA_DIR = Path("data")
DEFAULT_SESSION_MAX_AGE = 8 * 60 * 60


@dataclass(frozen=True)
class Settings:
    app_name: str
    database_url: str
    data_dir: Path
    session_secret: str
    session_https_only: bool
    session_max_age: int


def _env_flag(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes"}


def resolve_session_secret(data_dir: Path) -> str:
    """Use SESSION_SECRET, or a random secret stored beside the local database."""
    configured = os.environ.get("SESSION_SECRET", "").strip()
    if configured:
        return configured
    path = data_dir / "session_secret"
    try:
        existing = path.read_text(encoding="utf-8").strip()
    except OSError:
        existing = ""
    if existing:
        return existing
    path.parent.mkdir(parents=True, exist_ok=True)
    generated = secrets.token_hex(32)
    path.write_text(generated + "\n", encoding="utf-8")
    return generated


def load_settings() -> Settings:
    """Read process environment. Defaults match the original in-module constants."""
    data_dir = Path(os.environ.get("LEAVE_DATA_DIR", str(DEFAULT_DATA_DIR)))
    database_url = os.environ.get("DATABASE_URL", "").strip()
    if not database_url:
        if os.environ.get("LEAVE_DATA_DIR", "").strip():
            database_url = f"sqlite:///{(data_dir / 'leave.db').as_posix()}"
        else:
            database_url = DEFAULT_DATABASE_URL
    app_name = os.environ.get("APP_NAME", "").strip() or DEFAULT_APP_NAME
    return Settings(
        app_name=app_name,
        database_url=database_url,
        data_dir=data_dir,
        session_secret=resolve_session_secret(data_dir),
        session_https_only=_env_flag("SESSION_HTTPS_ONLY"),
        session_max_age=DEFAULT_SESSION_MAX_AGE,
    )


def get_settings() -> Settings:
    return load_settings()
