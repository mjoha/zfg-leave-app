from datetime import date

import pytest
from alembic.runtime.migration import MigrationContext
from sqlalchemy import inspect, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_engine, init_database, reset_database_state
from app.db_init import main
from app.models import LeaveRequest, User
from app.security import hash_password


def test_db_init_creates_schema_and_can_run_again(tmp_path, monkeypatch):
    database_file = tmp_path / "data" / "leave.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{database_file.as_posix()}")
    reset_database_state()
    try:
        main()
        assert database_file.exists()
        assert "users" in inspect(get_engine()).get_table_names()
        assert "leave_requests" in inspect(get_engine()).get_table_names()
        with get_engine().connect() as connection:
            assert MigrationContext.configure(connection).get_current_revision() == "0002_decision"
            columns = {column["name"] for column in inspect(get_engine()).get_columns("leave_requests")}
        assert {"decision_comment", "decided_at"} <= columns

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

        with pytest.raises(IntegrityError):
            with Session(get_engine()) as session:
                session.add(
                    LeaveRequest(
                        user_id=999999,
                        start_date=date(2001, 6, 12),
                        end_date=date(2001, 6, 12),
                        reason="Missing employee",
                        status="pending",
                    )
                )
                session.commit()
    finally:
        reset_database_state()
