from app.models import STATUS_APPROVED, STATUS_WITHDRAWN
from app.seed import DEMO_ADMIN_EMAIL, DEMO_ADMIN_PASSWORD, seed_database
from tests.test_leave_request import _login, _register, _rows, _submit
from tests.test_review_queue import _login_as


def test_stale_approval_does_not_overwrite_a_withdrawal(client):
    assert _register(client).status_code == 303
    assert _login(client).status_code == 303
    assert _submit(client, reason="Changed my mind").status_code == 303
    request_id = _rows()[0].id
    assert client.post(f"/requests/{request_id}/withdraw", follow_redirects=False).status_code == 303
    client.post("/logout", follow_redirects=False)
    seed_database()
    assert _login_as(client, DEMO_ADMIN_EMAIL, DEMO_ADMIN_PASSWORD).status_code == 303

    response = client.post(
        f"/requests/{request_id}/approve",
        data={"comment": "Too late", "expected_status": "pending"},
    )
    assert response.status_code == 400
    assert "changed since the form was opened" in response.text
    saved = _rows()[0]
    assert saved.status == STATUS_WITHDRAWN
    assert saved.decision_comment is None


def test_stale_rejection_does_not_overwrite_an_approval(client):
    seed_database()
    request_id = _rows()[0].id
    assert _login_as(client, DEMO_ADMIN_EMAIL, DEMO_ADMIN_PASSWORD).status_code == 303
    assert client.post(
        f"/requests/{request_id}/approve",
        data={"comment": "Go ahead", "expected_status": "pending"},
        follow_redirects=False,
    ).status_code == 303

    response = client.post(
        f"/requests/{request_id}/reject",
        data={"comment": "Actually no", "expected_status": "pending"},
    )
    assert response.status_code == 400
    assert "changed since the form was opened" in response.text
    saved = _rows()[0]
    assert saved.status == STATUS_APPROVED
    assert saved.decision_comment == "Go ahead"
