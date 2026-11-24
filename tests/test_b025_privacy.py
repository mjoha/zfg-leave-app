from app.seed import DEMO_ADMIN_EMAIL, DEMO_ADMIN_PASSWORD, seed_database
from tests.test_leave_request import _login, _register, _rows, _submit
from tests.test_review_queue import _login_as

PRIVATE = "Ada private trip"


def test_another_employee_cannot_read_a_private_request(client):
    assert _register(client).status_code == 303
    assert _login(client).status_code == 303
    assert _submit(client, start_date="2001-06-12", end_date="2001-06-12", reason=PRIVATE).status_code == 303
    request_id = _rows()[0].id
    client.post("/logout", follow_redirects=False)

    assert _register(client, email="grace@example.com", display_name="Grace Hopper").status_code == 303
    assert _login(client, email="grace@example.com").status_code == 303

    detail = client.get(f"/requests/{request_id}")
    edit = client.get(f"/requests/{request_id}/edit")
    posted = client.post(
        f"/requests/{request_id}/edit",
        data={"start_date": "2001-06-13", "end_date": "2001-06-13", "reason": "Changed"},
    )
    listing = client.get("/requests")
    month = client.get("/calendar?year=2001&month=6")
    week = client.get("/calendar/week?day=2001-06-12")
    for page in (detail, edit, posted, listing, month, week):
        assert PRIVATE not in page.text
    assert detail.status_code == 404
    assert edit.status_code == 404
    assert posted.status_code == 404
    assert _rows()[0].reason == PRIVATE
    assert _rows()[0].start_date.isoformat() == "2001-06-12"


def test_administrator_can_still_open_a_request_for_review(client):
    assert _register(client).status_code == 303
    assert _login(client).status_code == 303
    assert _submit(client, reason=PRIVATE).status_code == 303
    request_id = _rows()[0].id
    client.post("/logout", follow_redirects=False)
    seed_database()
    assert _login_as(client, DEMO_ADMIN_EMAIL, DEMO_ADMIN_PASSWORD).status_code == 303
    detail = client.get(f"/requests/{request_id}")
    assert detail.status_code == 200
    assert PRIVATE in detail.text
    assert 'data-testid="request-decision-form"' in detail.text
