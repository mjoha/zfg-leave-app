import os
from dataclasses import dataclass
from pathlib import Path

DEFAULT_APP_NAME = "leave-app"
DEFAULT_DATABASE_URL = "sqlite:///./data/leave.db"
DEFAULT_DATA_DIR = Path("data")


@dataclass(frozen=True)
class Settings:
    app_name: str
    database_url: str
    data_dir: Path


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
    return Settings(app_name=app_name, database_url=database_url, data_dir=data_dir)


def get_settings() -> Settings:
    return load_settings()
