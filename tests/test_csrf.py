from app.models import STATUS_PENDING
from app.seed import DEMO_ADMIN_EMAIL, DEMO_ADMIN_PASSWORD, seed_database
from tests.test_leave_request import _rows
from tests.test_review_queue import _login_as, decision_payload


def test_admin_decision_without_a_token_does_not_change_status(client):
    seed_database()
    request_id = _rows()[0].id
    assert _login_as(client, DEMO_ADMIN_EMAIL, DEMO_ADMIN_PASSWORD).status_code == 303
    response = client.post(
        f"/requests/{request_id}/approve",
        data={"comment": "Missing token", "expected_status": "pending"},
    )
    assert response.status_code == 403
    assert 'data-testid="csrf-error"' in response.text
    assert _rows()[0].status == STATUS_PENDING
    assert _rows()[0].decision_comment is None


def test_admin_decision_with_the_session_token_is_accepted(client):
    seed_database()
    request_id = _rows()[0].id
    assert _login_as(client, DEMO_ADMIN_EMAIL, DEMO_ADMIN_PASSWORD).status_code == 303
    response = client.post(
        f"/requests/{request_id}/reject",
        data=decision_payload(client, request_id, comment="With token"),
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert _rows()[0].decision_comment == "With token"


def test_wrong_token_is_rejected(client):
    seed_database()
    request_id = _rows()[0].id
    assert _login_as(client, DEMO_ADMIN_EMAIL, DEMO_ADMIN_PASSWORD).status_code == 303
    response = client.post(
        f"/requests/{request_id}/approve",
        data={"csrf_token": "not-the-session-token", "expected_status": "pending"},
    )
    assert response.status_code == 403
    assert 'data-testid="csrf-error"' in response.text
    assert _rows()[0].status == STATUS_PENDING
