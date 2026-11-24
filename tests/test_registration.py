from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_engine, reset_database_state
from app.main import app
from app.models import ROLE_EMPLOYEE, User
from app.security import verify_password


def _users() -> list[User]:
    with Session(get_engine()) as session:
        return list(session.scalars(select(User).order_by(User.id)))


def _register(client, **overrides):
    payload = {
        "email": "ada@example.com",
        "display_name": "Ada Lovelace",
        "password": "correct-horse",
        "password_confirm": "correct-horse",
    }
    payload.update(overrides)
    return client.post("/register", data=payload, follow_redirects=False)


def test_register_form_and_landing_link(client):
    landing = client.get("/")
    assert 'data-testid="landing-register"' in landing.text
    assert 'data-testid="nav-register"' in landing.text

    response = client.get("/register")
    assert response.status_code == 200
    body = response.text
    assert 'data-testid="register-form"' in body
    assert 'data-testid="register-email"' in body
    assert 'data-testid="register-display-name"' in body
    assert 'data-testid="register-password"' in body
    assert 'data-testid="register-password-confirm"' in body
    assert 'data-testid="register-submit"' in body
    assert 'for="email"' in body
    assert 'for="display_name"' in body


def test_successful_registration_stores_employee_with_hashed_password(client):
    response = _register(client, email="Ada@Example.com", role="administrator")

    assert response.status_code == 303
    assert response.headers["location"] == "/account-created"
    assert "correct-horse" not in response.headers["location"]

    created = client.get("/account-created")
    assert created.status_code == 200
    assert 'data-testid="registration-success"' in created.text
    assert "correct-horse" not in created.text

    users = _users()
    assert len(users) == 1
    user = users[0]
    assert user.email == "ada@example.com"
    assert user.display_name == "Ada Lovelace"
    assert user.role == ROLE_EMPLOYEE
    assert user.password_hash != "correct-horse"
    assert "correct-horse" not in user.password_hash
    assert verify_password("correct-horse", user.password_hash)
    assert not verify_password("wrong-password", user.password_hash)
    assert user.created_at is not None


def test_registration_rejects_invalid_input_without_saving(client):
    response = _register(
        client,
        email="not-an-email",
        display_name=" ",
        password="tiny",
        password_confirm="mismatch-secret-value",
    )

    assert response.status_code == 400
    body = response.text
    assert 'data-testid="register-error"' in body
    assert "valid email" in body
    assert "Display name" in body
    assert "Password must be between 8 and 128 characters." in body
    assert "does not match" in body
    assert "tiny" not in body
    assert "mismatch-secret-value" not in body
    assert 'value="not-an-email"' in body
    assert _users() == []


def test_control_characters_in_display_name_are_rejected(client):
    response = _register(client, display_name="Ada\nLovelace")

    assert response.status_code == 400
    assert "control characters" in response.text
    assert _users() == []


def test_duplicate_email_is_rejected(client):
    assert _register(client).status_code == 303
    again = _register(client, display_name="Another Ada")

    assert again.status_code == 400
    assert "already exists" in again.text
    assert len(_users()) == 1
    assert _users()[0].display_name == "Ada Lovelace"


def test_register_reports_missing_database(tmp_path, monkeypatch):
    database_file = tmp_path / "missing-dir" / "leave.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{database_file.as_posix()}")
    reset_database_state()
    try:
        with TestClient(app) as client:
            response = _register(client)
        assert response.status_code == 503
        assert 'data-testid="database-unavailable"' in response.text
        assert not database_file.exists()
    finally:
        reset_database_state()
