"""Stable data-testid markers used by later browser automation."""

from fastapi.testclient import TestClient

from app.database import reset_database_state
from app.main import app

SIGNED_OUT_HOME = (
    "brand-link",
    "nav-home",
    "nav-register",
    "nav-login",
    "landing-title",
    "landing-summary",
    "landing-register",
    "landing-login",
)
REGISTER_FORM = (
    "register-form",
    "register-email",
    "register-display-name",
    "register-password",
    "register-password-confirm",
    "register-submit",
)
LOGIN_FORM = (
    "login-form",
    "login-email",
    "login-password",
    "login-submit",
)
SIGNED_IN_NAV = (
    "brand-link",
    "nav-home",
    "nav-requests",
    "nav-new-request",
    "nav-profile",
    "nav-user",
    "logout-form",
    "logout-submit",
    "signed-in-name",
)
PROFILE = (
    "profile-display-name",
    "profile-email",
    "profile-role",
    "profile-created",
    "profile-form",
    "profile-display-name-input",
    "profile-submit",
)


def _assert_selectors(body: str, selectors: tuple[str, ...]) -> None:
    for selector in selectors:
        assert f'data-testid="{selector}"' in body


def test_signed_out_pages_expose_selectors(client):
    _assert_selectors(client.get("/").text, SIGNED_OUT_HOME)
    _assert_selectors(client.get("/register").text, REGISTER_FORM)
    _assert_selectors(client.get("/login").text, LOGIN_FORM)
    created = client.get("/account-created")
    _assert_selectors(created.text, ("registration-success", "registration-success-login", "registration-success-home"))
    missing = client.get("/missing-page")
    assert missing.status_code == 404
    _assert_selectors(missing.text, ("not-found", "not-found-home"))


def test_signed_in_pages_expose_selectors(client):
    assert client.post(
        "/register",
        data={
            "email": "ada@example.com",
            "display_name": "Ada Lovelace",
            "password": "correct-horse",
            "password_confirm": "correct-horse",
        },
        follow_redirects=False,
    ).status_code == 303
    assert client.post(
        "/login",
        data={"email": "ada@example.com", "password": "correct-horse"},
        follow_redirects=False,
    ).status_code == 303

    _assert_selectors(client.get("/").text, SIGNED_IN_NAV)
    profile = client.get("/profile")
    _assert_selectors(profile.text, PROFILE)
    _assert_selectors(profile.text, ("nav-profile", "logout-submit"))


def test_validation_states_expose_selectors(client):
    invalid = client.post(
        "/register",
        data={
            "email": "not-an-email",
            "display_name": "Ada Lovelace",
            "password": "correct-horse",
            "password_confirm": "correct-horse",
        },
    )
    assert invalid.status_code == 400
    _assert_selectors(invalid.text, ("register-error",))

    assert client.post(
        "/register",
        data={
            "email": "ada@example.com",
            "display_name": "Ada Lovelace",
            "password": "correct-horse",
            "password_confirm": "correct-horse",
        },
        follow_redirects=False,
    ).status_code == 303
    rejected = client.post(
        "/login",
        data={"email": "ada@example.com", "password": "wrong-password"},
    )
    assert rejected.status_code == 400
    _assert_selectors(rejected.text, ("login-error",))

    assert client.post(
        "/login",
        data={"email": "ada@example.com", "password": "correct-horse"},
        follow_redirects=False,
    ).status_code == 303
    blank = client.post("/profile", data={"display_name": " "})
    assert blank.status_code == 400
    _assert_selectors(blank.text, ("profile-error",))
    saved = client.post("/profile", data={"display_name": "Ada King"}, follow_redirects=True)
    assert saved.status_code == 200
    _assert_selectors(saved.text, ("profile-saved",))


def test_database_unavailable_page_exposes_selector(tmp_path, monkeypatch):
    database_file = tmp_path / "missing-dir" / "leave.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{database_file.as_posix()}")
    reset_database_state()
    try:
        with TestClient(app) as bare_client:
            response = bare_client.post(
                "/login",
                data={"email": "ada@example.com", "password": "correct-horse"},
            )
        assert response.status_code == 503
        _assert_selectors(response.text, ("database-unavailable", "database-unavailable-register"))
    finally:
        reset_database_state()
