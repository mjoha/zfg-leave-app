from fastapi.testclient import TestClient

from app.database import reset_database_state
from app.main import app


def _register(client, **overrides):
    payload = {
        "email": "ada@example.com",
        "display_name": "Ada Lovelace",
        "password": "correct-horse",
        "password_confirm": "correct-horse",
    }
    payload.update(overrides)
    return client.post("/register", data=payload, follow_redirects=False)


def _login(client, **overrides):
    payload = {"email": "ada@example.com", "password": "correct-horse"}
    payload.update(overrides)
    return client.post("/login", data=payload, follow_redirects=False)


def test_login_form_is_available_when_signed_out(client):
    response = client.get("/login")

    assert response.status_code == 200
    body = response.text
    assert 'data-testid="login-form"' in body
    assert 'data-testid="login-email"' in body
    assert 'data-testid="login-password"' in body
    assert 'data-testid="login-submit"' in body
    assert 'data-testid="nav-login"' in body
    home = client.get("/")
    assert 'data-testid="landing-login"' in home.text


def test_registration_does_not_start_a_session(client):
    assert _register(client).status_code == 303
    created = client.get("/account-created")
    assert 'data-testid="registration-success-login"' in created.text
    home = client.get("/")
    assert 'data-testid="signed-in-name"' not in home.text
    assert 'data-testid="nav-login"' in home.text


def test_login_sets_a_local_session_cookie(client):
    assert _register(client).status_code == 303
    response = _login(client, email="Ada@Example.com")

    assert response.status_code == 303
    assert response.headers["location"] == "/profile"
    cookie = response.headers["set-cookie"].lower()
    assert "leave_session=" in cookie
    assert "httponly" in cookie
    assert "samesite=lax" in cookie
    assert "max-age=28800" in cookie
    assert "; secure" not in cookie
    assert "correct-horse" not in cookie

    home = client.get("/")
    assert 'data-testid="signed-in-name"' in home.text
    assert "Ada Lovelace" in home.text
    assert 'data-testid="nav-user"' in home.text
    assert 'data-testid="logout-submit"' in home.text
    assert 'data-testid="nav-login"' not in home.text
    assert 'data-testid="nav-register"' not in home.text


def test_login_rejects_unknown_email_and_wrong_password(client):
    assert _register(client).status_code == 303

    unknown = _login(client, email="missing@example.com")
    assert unknown.status_code == 400
    assert 'data-testid="login-error"' in unknown.text
    assert "incorrect" in unknown.text
    assert "correct-horse" not in unknown.text

    wrong = _login(client, password="wrong-password")
    assert wrong.status_code == 400
    assert "incorrect" in wrong.text
    assert "wrong-password" not in wrong.text
    assert 'value="ada@example.com"' in wrong.text

    home = client.get("/")
    assert 'data-testid="signed-in-name"' not in home.text


def test_login_requires_email_and_password(client):
    response = _login(client, email=" ", password="")

    assert response.status_code == 400
    assert "Enter your email and password." in response.text


def test_logout_clears_the_session(client):
    assert _register(client).status_code == 303
    assert _login(client).status_code == 303

    response = client.post("/logout", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/"
    home = client.get("/")
    assert 'data-testid="signed-in-name"' not in home.text
    assert 'data-testid="nav-login"' in home.text


def test_login_page_redirects_when_already_signed_in(client):
    assert _register(client).status_code == 303
    assert _login(client).status_code == 303

    response = client.get("/login", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/profile"


def test_login_reports_missing_database(tmp_path, monkeypatch):
    database_file = tmp_path / "missing-dir" / "leave.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{database_file.as_posix()}")
    reset_database_state()
    try:
        with TestClient(app) as client:
            response = _login(client)
        assert response.status_code == 503
        assert 'data-testid="database-unavailable"' in response.text
    finally:
        reset_database_state()
