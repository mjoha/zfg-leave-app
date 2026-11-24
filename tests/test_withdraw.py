from app.models import STATUS_PENDING, STATUS_WITHDRAWN
from tests.test_leave_request import _login, _register, _rows, _submit


def test_owner_can_withdraw_a_pending_request(client):
    assert _register(client).status_code == 303
    assert _login(client).status_code == 303
    assert _submit(client).status_code == 303
    request_id = _rows()[0].id

    detail = client.get(f"/requests/{request_id}")
    assert 'data-testid="request-withdraw"' in detail.text

    response = client.post(f"/requests/{request_id}/withdraw", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == f"/requests/{request_id}?withdrawn=1"

    withdrawn = client.get(response.headers["location"])
    assert 'data-testid="request-withdrawn"' in withdrawn.text
    assert "Withdrawn" in withdrawn.text
    assert 'data-testid="request-withdraw"' not in withdrawn.text

    listing = client.get("/requests")
    assert listing.text.count('data-testid="request-status"') == 1
    assert "Withdrawn" in listing.text
    assert _rows()[0].status == STATUS_WITHDRAWN


def test_withdraw_rejects_a_request_that_is_not_pending(client):
    assert _register(client).status_code == 303
    assert _login(client).status_code == 303
    assert _submit(client).status_code == 303
    request_id = _rows()[0].id
    assert client.post(f"/requests/{request_id}/withdraw", follow_redirects=False).status_code == 303

    again = client.post(f"/requests/{request_id}/withdraw")
    assert again.status_code == 400
    assert 'data-testid="request-error"' in again.text
    assert "pending" in again.text
    assert _rows()[0].status == STATUS_WITHDRAWN


def test_another_user_cannot_withdraw_the_request(client):
    assert _register(client).status_code == 303
    assert _login(client).status_code == 303
    assert _submit(client, reason="Ada private trip").status_code == 303
    request_id = _rows()[0].id
    client.post("/logout", follow_redirects=False)

    assert _register(client, email="grace@example.com", display_name="Grace Hopper").status_code == 303
    assert _login(client, email="grace@example.com").status_code == 303
    hidden = client.post(f"/requests/{request_id}/withdraw")
    assert hidden.status_code == 404
    assert "Ada private trip" not in hidden.text
    assert _rows()[0].status == STATUS_PENDING


def test_withdraw_requires_sign_in(client):
    response = client.post("/requests/1/withdraw", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/login"
