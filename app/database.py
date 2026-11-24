import os
from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

DEFAULT_DATABASE_URL = "sqlite:///./data/leave.db"

_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None


class Base(DeclarativeBase):
    pass


def current_database_url() -> str:
    return os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL)


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
        _session_factory = sessionmaker(bind=_engine, autoflush=False, autocommit=False)
    return _engine


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
    """Create missing tables. Existing rows are left in place."""
    from app import models  # noqa: F401

    path = sqlite_file_path(current_database_url())
    if path is not None and str(path.parent) not in {"", "."}:
        path.parent.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=get_engine())
