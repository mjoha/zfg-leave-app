from sqlalchemy import inspect, select
from sqlalchemy.orm import Session

from app.database import get_engine, init_database, reset_database_state
from app.db_init import main
from app.models import User
from app.security import hash_password


def test_db_init_creates_schema_and_can_run_again(tmp_path, monkeypatch):
    database_file = tmp_path / "data" / "leave.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{database_file.as_posix()}")
    reset_database_state()
    try:
        main()
        assert database_file.exists()
        assert "users" in inspect(get_engine()).get_table_names()

        with Session(get_engine()) as session:
            session.add(
                User(
                    email="kept@example.com",
                    display_name="Kept User",
                    password_hash=hash_password("kept-secret"),
                )
            )
            session.commit()

        init_database()
        with Session(get_engine()) as session:
            saved = session.scalars(select(User)).one()
        assert saved.email == "kept@example.com"
        assert saved.role == "employee"
    finally:
        reset_database_state()
