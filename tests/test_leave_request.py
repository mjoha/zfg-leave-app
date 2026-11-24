import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_engine, reset_database_state
from app.models import STATUS_PENDING, LeaveRequest


def _register(client, email="ada@example.com", display_name="Ada Lovelace"):
    return client.post(
        "/register",
        data={
            "email": email,
            "display_name": display_name,
            "password": "correct-horse",
            "password_confirm": "correct-horse",
        },
        follow_redirects=False,
    )


def _login(client, email="ada@example.com"):
    return client.post(
        "/login",
        data={"email": email, "password": "correct-horse"},
        follow_redirects=False,
    )


def _form_token(client) -> str:
    page = client.get("/requests/new")
    match = re.search(r'name="form_token" value="([^"]+)"', page.text)
    assert match is not None
    return match.group(1)


def _submit(client, **overrides):
    payload = {
        "start_date": "2001-06-12",
        "end_date": "2001-06-14",
        "reason": "Family visit",
        "user_id": "999",
    }
    payload.update(overrides)
    if "form_token" not in payload:
        payload["form_token"] = _form_token(client)
    response = client.post("/requests", data=payload, follow_redirects=False)
    if response.status_code == 200 and 'data-testid="request-confirm"' in response.text:
        return client.post("/requests/confirm", follow_redirects=False)
    return response


def _rows() -> list[LeaveRequest]:
    with Session(get_engine()) as session:
        return list(session.scalars(select(LeaveRequest).order_by(LeaveRequest.id)))


def test_request_form_requires_sign_in(client):
    response = client.get("/requests/new", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/login"

    posted = _submit(client, form_token="unsigned")
    assert posted.status_code == 303
    assert posted.headers["location"] == "/login"
    assert _rows() == []


def test_signed_in_user_can_create_a_pending_request(client):
    assert _register(client).status_code == 303
    assert _login(client).status_code == 303

    form = client.get("/requests/new")
    assert form.status_code == 200
    assert 'data-testid="request-form"' in form.text
    assert 'data-testid="nav-new-request"' in form.text

    response = _submit(client)
    assert response.status_code == 303
    assert response.headers["location"] == "/requests?saved=1"

    created = client.get(response.headers["location"])
    assert created.status_code == 200
    assert 'data-testid="request-saved"' in created.text
    assert 'data-testid="request-list"' in created.text
    assert "2001-06-12 to 2001-06-14" in created.text
    assert "3" in created.text

    rows = _rows()
    assert len(rows) == 1
    assert rows[0].start_date.isoformat() == "2001-06-12"
    assert rows[0].end_date.isoformat() == "2001-06-14"
    assert rows[0].reason == "Family visit"
    assert rows[0].status == STATUS_PENDING
    assert rows[0].user_id != 999


def test_end_date_before_start_is_rejected(client):
    assert _register(client).status_code == 303
    assert _login(client).status_code == 303

    response = _submit(client, start_date="2001-06-14", end_date="2001-06-12")

    assert response.status_code == 400
    assert 'data-testid="request-error"' in response.text
    assert "on or after the start date" in response.text
    assert _rows() == []


def test_invalid_reason_and_dates_are_rejected(client):
    assert _register(client).status_code == 303
    assert _login(client).status_code == 303

    response = _submit(client, start_date="June", end_date="", reason=" ")

    assert response.status_code == 400
    body = response.text
    assert "start date" in body
    assert "end date" in body
    assert "Reason" in body
    assert _rows() == []


def test_list_shows_only_the_signed_in_users_requests(client):
    assert _register(client).status_code == 303
    assert _login(client).status_code == 303
    assert _submit(client, reason="Ada trip").status_code == 303
    client.post("/logout", follow_redirects=False)

    assert _register(client, email="grace@example.com", display_name="Grace Hopper").status_code == 303
    assert _login(client, email="grace@example.com").status_code == 303
    empty = client.get("/requests")
    assert empty.status_code == 200
    assert 'data-testid="request-empty"' in empty.text
    assert "Ada trip" not in empty.text
    assert 'data-testid="nav-requests"' in empty.text

    assert _submit(client, start_date="2001-07-02", end_date="2001-07-02", reason="Grace day").status_code == 303
    grace_list = client.get("/requests")
    assert grace_list.text.count('data-testid="request-row"') == 1
    assert "Grace day" in grace_list.text
    assert "Ada trip" not in grace_list.text
    assert "Pending" in grace_list.text

    client.post("/logout", follow_redirects=False)
    assert _login(client, email="ada@example.com").status_code == 303
    ada_list = client.get("/requests")
    assert "Ada trip" in ada_list.text
    assert "Grace day" not in ada_list.text


def test_requests_page_requires_sign_in(client):
    response = client.get("/requests", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_submit_reports_missing_database(client, tmp_path, monkeypatch):
    assert _register(client).status_code == 303
    assert _login(client).status_code == 303
    token = _form_token(client)
    database_file = tmp_path / "missing-dir" / "leave.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{database_file.as_posix()}")
    reset_database_state()
    try:
        response = _submit(client, form_token=token)
        assert response.status_code == 503
        assert 'data-testid="database-unavailable"' in response.text
    finally:
        reset_database_state()
