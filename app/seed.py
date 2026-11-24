"""Deterministic fictional accounts for a local demo. Not real people."""

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_engine, init_database
from app.leave import LeaveRequestInput, create_leave_request
from app.models import ROLE_ADMINISTRATOR, ROLE_EMPLOYEE, LeaveRequest, User
from app.security import hash_password

SEED_VERSION = "1"

DEMO_EMPLOYEE_EMAIL = "employee@example.com"
DEMO_EMPLOYEE_PASSWORD = "employee-demo-pass"
DEMO_EMPLOYEE_NAME = "Demo Employee"

DEMO_ADMIN_EMAIL = "admin@example.com"
DEMO_ADMIN_PASSWORD = "admin-demo-pass"
DEMO_ADMIN_NAME = "Demo Administrator"

SAMPLE_START = date(2001, 6, 12)
SAMPLE_END = date(2001, 6, 14)
SAMPLE_REASON = "Demo trip"


def _ensure_user(db: Session, *, email: str, display_name: str, password: str, role: str) -> User:
    existing = db.scalar(select(User).where(User.email == email))
    if existing is not None:
        return existing
    user = User(
        email=email,
        display_name=display_name,
        password_hash=hash_password(password),
        role=role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def seed_database() -> None:
    """Create missing tables, then ensure the demo accounts and sample request exist."""
    init_database()
    db = Session(get_engine())
    try:
        employee = _ensure_user(
            db,
            email=DEMO_EMPLOYEE_EMAIL,
            display_name=DEMO_EMPLOYEE_NAME,
            password=DEMO_EMPLOYEE_PASSWORD,
            role=ROLE_EMPLOYEE,
        )
        _ensure_user(
            db,
            email=DEMO_ADMIN_EMAIL,
            display_name=DEMO_ADMIN_NAME,
            password=DEMO_ADMIN_PASSWORD,
            role=ROLE_ADMINISTRATOR,
        )
        sample = db.scalar(
            select(LeaveRequest).where(
                LeaveRequest.user_id == employee.id,
                LeaveRequest.start_date == SAMPLE_START,
                LeaveRequest.end_date == SAMPLE_END,
                LeaveRequest.reason == SAMPLE_REASON,
            )
        )
        if sample is None:
            create_leave_request(
                db,
                employee.id,
                LeaveRequestInput(SAMPLE_START, SAMPLE_END, SAMPLE_REASON),
            )
    finally:
        db.close()


def main() -> None:
    seed_database()
    print(f"Demo data is ready (seed version {SEED_VERSION}).")


if __name__ == "__main__":
    main()
