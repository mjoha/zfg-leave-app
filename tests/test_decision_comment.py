from app.seed import DEMO_ADMIN_EMAIL, DEMO_ADMIN_PASSWORD, DEMO_EMPLOYEE_EMAIL, DEMO_EMPLOYEE_PASSWORD, seed_database
from tests.test_leave_request import _rows
from tests.test_review_queue import _login_as, decision_payload


def test_approval_comment_is_stored_and_shown_escaped(client):
    seed_database()
    request_id = _rows()[0].id
    assert _login_as(client, DEMO_ADMIN_EMAIL, DEMO_ADMIN_PASSWORD).status_code == 303
    response = client.post(
        f"/requests/{request_id}/approve",
        data=decision_payload(client, request_id, comment="Approved for <trip>"),
        follow_redirects=False,
    )
    assert response.status_code == 303
    saved = _rows()[0]
    assert saved.decision_comment == "Approved for <trip>"
    assert saved.decided_at is not None

    detail = client.get(f"/requests/{request_id}")
    assert 'data-testid="request-decision-comment"' in detail.text
    assert "Approved for &lt;trip&gt;" in detail.text
    assert "Approved for <trip>" not in detail.text

    client.post("/logout", follow_redirects=False)
    assert _login_as(client, DEMO_EMPLOYEE_EMAIL, DEMO_EMPLOYEE_PASSWORD).status_code == 303
    employee = client.get(f"/requests/{request_id}")
    assert "Approved for &lt;trip&gt;" in employee.text


def test_blank_comment_is_allowed(client):
    seed_database()
    request_id = _rows()[0].id
    assert _login_as(client, DEMO_ADMIN_EMAIL, DEMO_ADMIN_PASSWORD).status_code == 303
    response = client.post(
        f"/requests/{request_id}/reject",
        data=decision_payload(client, request_id, comment="   "),
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert _rows()[0].decision_comment is None
    detail = client.get(f"/requests/{request_id}")
    assert 'data-testid="request-decision-comment"' not in detail.text
    assert "Rejected" in detail.text


def test_overlong_comment_does_not_decide_the_request(client):
    seed_database()
    request_id = _rows()[0].id
    assert _login_as(client, DEMO_ADMIN_EMAIL, DEMO_ADMIN_PASSWORD).status_code == 303
    response = client.post(
        f"/requests/{request_id}/approve",
        data=decision_payload(client, request_id, comment="x" * 501),
    )
    assert response.status_code == 400
    assert "500 characters" in response.text
    assert 'data-testid="request-decision-comment-input"' in response.text
    assert _rows()[0].status == "pending"
    assert _rows()[0].decision_comment is None
