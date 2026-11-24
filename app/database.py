from collections.abc import Generator
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings

ROOT = Path(__file__).resolve().parents[1]

_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None


class Base(DeclarativeBase):
    pass


def current_database_url() -> str:
    return get_settings().database_url


def reset_database_state() -> None:
    """Drop the cached engine so a new DATABASE_URL can take effect."""
    global _engine, _session_factory
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _session_factory = None


def get_engine() -> Engine:
    global _engine, _session_factory
    if _engine is None:
        url = current_database_url()
        connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
        _engine = create_engine(url, connect_args=connect_args)
        if url.startswith("sqlite"):
            event.listen(_engine, "connect", _enable_sqlite_foreign_keys)
        _session_factory = sessionmaker(bind=_engine, autoflush=False, autocommit=False)
    return _engine


def _enable_sqlite_foreign_keys(dbapi_connection, connection_record) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def get_db() -> Generator[Session, None, None]:
    get_engine()
    if _session_factory is None:
        raise RuntimeError("Database session factory was not initialized.")
    db = _session_factory()
    try:
        yield db
    finally:
        db.close()


def sqlite_file_path(url: str) -> Path | None:
    if not url.startswith("sqlite:///") or url.endswith(":memory:"):
        return None
    raw = url.removeprefix("sqlite:///")
    if raw.startswith(":memory:"):
        return None
    return Path(raw)


def init_database() -> None:
    """Apply Alembic migrations. Existing rows are left in place."""
    path = sqlite_file_path(current_database_url())
    if path is not None and str(path.parent) not in {"", "."}:
        path.parent.mkdir(parents=True, exist_ok=True)
    config = Config(str(ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(ROOT / "alembic"))
    config.set_main_option("sqlalchemy.url", current_database_url().replace("%", "%%"))
    command.upgrade(config, "head")
