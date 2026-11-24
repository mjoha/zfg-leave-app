from app.models import STATUS_PENDING, STATUS_WITHDRAWN
from tests.test_leave_request import _login, _register, _rows, _submit


def test_owner_can_edit_a_pending_request(client):
    assert _register(client).status_code == 303
    assert _login(client).status_code == 303
    assert _submit(client).status_code == 303
    request_id = _rows()[0].id

    detail = client.get(f"/requests/{request_id}")
    assert 'data-testid="request-edit"' in detail.text
    form = client.get(f"/requests/{request_id}/edit")
    assert form.status_code == 200
    assert 'data-testid="request-edit-form"' in form.text
    assert "2001-06-12" in form.text
    assert "Family visit" in form.text

    response = client.post(
        f"/requests/{request_id}/edit",
        data={"start_date": "2001-07-02", "end_date": "2001-07-04", "reason": "Changed plans"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"] == f"/requests/{request_id}?edited=1"
    saved = client.get(response.headers["location"])
    assert 'data-testid="request-edited"' in saved.text
    assert "2001-07-02 to 2001-07-04" in saved.text
    assert "Changed plans" in saved.text
    row = _rows()[0]
    assert row.status == STATUS_PENDING
    assert row.reason == "Changed plans"


def test_edit_rejects_an_end_date_before_the_start(client):
    assert _register(client).status_code == 303
    assert _login(client).status_code == 303
    assert _submit(client).status_code == 303
    request_id = _rows()[0].id
    response = client.post(
        f"/requests/{request_id}/edit",
        data={"start_date": "2001-07-04", "end_date": "2001-07-02", "reason": "Backwards"},
    )
    assert response.status_code == 400
    assert "on or after the start date" in response.text
    assert _rows()[0].reason == "Family visit"


def test_withdrawn_request_cannot_be_edited(client):
    assert _register(client).status_code == 303
    assert _login(client).status_code == 303
    assert _submit(client).status_code == 303
    request_id = _rows()[0].id
    assert client.post(f"/requests/{request_id}/withdraw", follow_redirects=False).status_code == 303
    response = client.post(
        f"/requests/{request_id}/edit",
        data={"start_date": "2001-08-01", "end_date": "2001-08-02", "reason": "Too late"},
    )
    assert response.status_code == 400
    assert "pending" in response.text
    assert _rows()[0].status == STATUS_WITHDRAWN
    assert _rows()[0].reason == "Family visit"


def test_another_user_cannot_edit_the_request(client):
    assert _register(client).status_code == 303
    assert _login(client).status_code == 303
    assert _submit(client, reason="Ada private trip").status_code == 303
    request_id = _rows()[0].id
    client.post("/logout", follow_redirects=False)
    assert _register(client, email="grace@example.com", display_name="Grace Hopper").status_code == 303
    assert _login(client, email="grace@example.com").status_code == 303
    hidden = client.get(f"/requests/{request_id}/edit")
    assert hidden.status_code == 404
    assert "Ada private trip" not in hidden.text
    posted = client.post(
        f"/requests/{request_id}/edit",
        data={"start_date": "2001-08-01", "end_date": "2001-08-02", "reason": "Not mine"},
    )
    assert posted.status_code == 404
    assert _rows()[0].reason == "Ada private trip"


def test_edit_requires_sign_in(client):
    response = client.get("/requests/1/edit", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/login"
