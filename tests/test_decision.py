from app.models import STATUS_APPROVED, STATUS_PENDING, STATUS_REJECTED
from app.seed import DEMO_ADMIN_EMAIL, DEMO_ADMIN_PASSWORD, DEMO_EMPLOYEE_EMAIL, DEMO_EMPLOYEE_PASSWORD, seed_database
from tests.test_leave_request import _login, _register, _rows, _submit
from tests.test_review_queue import _login_as


def test_administrator_can_approve_a_pending_request(client):
    seed_database()
    request_id = _rows()[0].id
    assert _login_as(client, DEMO_ADMIN_EMAIL, DEMO_ADMIN_PASSWORD).status_code == 303
    detail = client.get(f"/requests/{request_id}")
    assert 'data-testid="request-approve"' in detail.text
    assert 'data-testid="request-reject"' in detail.text

    response = client.post(f"/requests/{request_id}/approve", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == f"/requests/{request_id}?decided=approved"
    saved = client.get(response.headers["location"])
    assert 'data-testid="request-decided"' in saved.text
    assert "Approved" in saved.text
    assert 'data-testid="request-approve"' not in saved.text
    assert _rows()[0].status == STATUS_APPROVED

    queue = client.get("/reviews")
    assert 'data-testid="review-empty"' in queue.text
    client.post("/logout", follow_redirects=False)
    assert _login_as(client, DEMO_EMPLOYEE_EMAIL, DEMO_EMPLOYEE_PASSWORD).status_code == 303
    mine = client.get("/requests")
    assert "Approved" in mine.text
    assert "Demo trip" in mine.text


def test_administrator_can_reject_a_pending_request(client):
    assert _register(client).status_code == 303
    assert _login(client).status_code == 303
    assert _submit(client, reason="Needs a decision").status_code == 303
    request_id = _rows()[0].id
    client.post("/logout", follow_redirects=False)
    seed_database()
    assert _login_as(client, DEMO_ADMIN_EMAIL, DEMO_ADMIN_PASSWORD).status_code == 303

    response = client.post(f"/requests/{request_id}/reject", follow_redirects=False)
    assert response.status_code == 303
    assert _rows()[0].status == STATUS_REJECTED
    detail = client.get(f"/requests/{request_id}")
    assert "Rejected" in detail.text
    assert "Needs a decision" in detail.text


def test_employee_cannot_approve_or_reject(client):
    seed_database()
    request_id = _rows()[0].id
    assert _login_as(client, DEMO_EMPLOYEE_EMAIL, DEMO_EMPLOYEE_PASSWORD).status_code == 303
    detail = client.get(f"/requests/{request_id}")
    assert 'data-testid="request-approve"' not in detail.text
    approved = client.post(f"/requests/{request_id}/approve")
    rejected = client.post(f"/requests/{request_id}/reject")
    assert approved.status_code == 403
    assert rejected.status_code == 403
    assert _rows()[0].status == STATUS_PENDING


def test_a_request_can_be_decided_only_once(client):
    seed_database()
    request_id = _rows()[0].id
    assert _login_as(client, DEMO_ADMIN_EMAIL, DEMO_ADMIN_PASSWORD).status_code == 303
    assert client.post(f"/requests/{request_id}/approve", follow_redirects=False).status_code == 303
    again = client.post(f"/requests/{request_id}/reject")
    assert again.status_code == 400
    assert "pending" in again.text
    assert _rows()[0].status == STATUS_APPROVED


def test_decision_requires_sign_in(client):
    response = client.post("/requests/1/approve", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/login"
