from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_engine
from app.models import User


def _register(client):
    return client.post(
        "/register",
        data={
            "email": "ada@example.com",
            "display_name": "Ada Lovelace",
            "password": "correct-horse",
            "password_confirm": "correct-horse",
        },
        follow_redirects=False,
    )


def _login(client):
    return client.post(
        "/login",
        data={"email": "ada@example.com", "password": "correct-horse"},
        follow_redirects=False,
    )


def _stored_name() -> str:
    with Session(get_engine()) as session:
        user = session.scalars(select(User)).one()
        return user.display_name


def test_profile_requires_sign_in(client):
    response = client.get("/profile", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/login"

    posted = client.post(
        "/profile",
        data={"display_name": "Someone Else", "email": "other@example.com", "role": "administrator"},
        follow_redirects=False,
    )
    assert posted.status_code == 303
    assert posted.headers["location"] == "/login"


def test_profile_shows_account_details_and_saves_display_name(client):
    assert _register(client).status_code == 303
    assert _login(client).status_code == 303

    page = client.get("/profile")
    assert page.status_code == 200
    body = page.text
    assert 'data-testid="nav-profile"' in body
    assert 'data-testid="profile-display-name"' in body
    assert "Ada Lovelace" in body
    assert 'data-testid="profile-email"' in body
    assert "ada@example.com" in body
    assert 'data-testid="profile-role"' in body
    assert ">Employee<" in body
    assert 'data-testid="profile-created"' in body
    assert 'data-testid="profile-form"' in body
    assert 'data-testid="profile-display-name-input"' in body
    assert 'data-testid="profile-submit"' in body

    saved = client.post(
        "/profile",
        data={
            "display_name": "Ada King",
            "email": "intruder@example.com",
            "role": "administrator",
        },
        follow_redirects=False,
    )
    assert saved.status_code == 303
    assert saved.headers["location"] == "/profile?saved=1"

    updated = client.get("/profile?saved=1")
    assert 'data-testid="profile-saved"' in updated.text
    assert 'data-testid="profile-display-name">Ada King<' in updated.text
    assert "ada@example.com" in updated.text
    assert ">Employee<" in updated.text
    assert _stored_name() == "Ada King"

    home = client.get("/")
    assert "Signed in as Ada King." in home.text


def test_profile_rejects_a_blank_display_name(client):
    assert _register(client).status_code == 303
    assert _login(client).status_code == 303

    response = client.post("/profile", data={"display_name": " "}, follow_redirects=False)

    assert response.status_code == 400
    assert 'data-testid="profile-error"' in response.text
    assert "Display name" in response.text
    assert 'data-testid="profile-display-name">Ada Lovelace<' in response.text
    assert _stored_name() == "Ada Lovelace"
