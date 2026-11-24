from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_engine
from app.models import ROLE_ADMINISTRATOR, ROLE_EMPLOYEE, LeaveRequest, User
from app.security import verify_password
from app.seed import (
    DEMO_ADMIN_EMAIL,
    DEMO_ADMIN_PASSWORD,
    DEMO_EMPLOYEE_EMAIL,
    DEMO_EMPLOYEE_PASSWORD,
    SAMPLE_REASON,
    SEED_VERSION,
    seed_database,
)


def _count(model) -> int:
    with Session(get_engine()) as session:
        return session.scalar(select(func.count()).select_from(model))


def test_seed_creates_demo_accounts_once(client):
    assert SEED_VERSION == "1"
    seed_database()
    seed_database()

    assert _count(User) == 2
    assert _count(LeaveRequest) == 1

    with Session(get_engine()) as session:
        employee = session.scalars(select(User).where(User.email == DEMO_EMPLOYEE_EMAIL)).one()
        admin = session.scalars(select(User).where(User.email == DEMO_ADMIN_EMAIL)).one()
        assert employee.role == ROLE_EMPLOYEE
        assert admin.role == ROLE_ADMINISTRATOR
        assert verify_password(DEMO_EMPLOYEE_PASSWORD, employee.password_hash)
        assert verify_password(DEMO_ADMIN_PASSWORD, admin.password_hash)
        request = session.scalars(select(LeaveRequest)).one()
        assert request.user_id == employee.id
        assert request.reason == SAMPLE_REASON
        assert request.start_date.isoformat() == "2001-06-12"
        assert request.end_date.isoformat() == "2001-06-14"

    employee_login = client.post(
        "/login",
        data={"email": DEMO_EMPLOYEE_EMAIL, "password": DEMO_EMPLOYEE_PASSWORD},
        follow_redirects=False,
    )
    assert employee_login.status_code == 303
    employee_list = client.get("/requests")
    assert SAMPLE_REASON in employee_list.text

    client.post("/logout", follow_redirects=False)
    admin_login = client.post(
        "/login",
        data={"email": DEMO_ADMIN_EMAIL, "password": DEMO_ADMIN_PASSWORD},
        follow_redirects=False,
    )
    assert admin_login.status_code == 303
    admin_profile = client.get("/profile")
    assert "Administrator" in admin_profile.text
    admin_list = client.get("/requests")
    assert 'data-testid="request-empty"' in admin_list.text
    assert SAMPLE_REASON not in admin_list.text
