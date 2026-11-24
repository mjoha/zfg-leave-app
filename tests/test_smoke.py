"""HTTP walk through the demo accounts: request, review, decision, timeline."""

from app.models import STATUS_APPROVED
from app.seed import (
    DEMO_ADMIN_EMAIL,
    DEMO_ADMIN_PASSWORD,
    DEMO_EMPLOYEE_EMAIL,
    DEMO_EMPLOYEE_PASSWORD,
    seed_database,
)
from tests.test_leave_request import _rows
from tests.test_review_queue import _login_as


def test_demo_request_can_be_reviewed_and_approved(client):
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json() == {"status": "ok"}

    seed_database()
    request_id = _rows()[0].id

    assert _login_as(client, DEMO_EMPLOYEE_EMAIL, DEMO_EMPLOYEE_PASSWORD).status_code == 303
    mine = client.get("/requests")
    assert "Demo trip" in mine.text
    assert "Pending" in mine.text
    detail = client.get(f"/requests/{request_id}")
    assert "Submitted" in detail.text
    assert 'data-testid="request-withdraw"' in detail.text
    client.post("/logout", follow_redirects=False)

    assert _login_as(client, DEMO_ADMIN_EMAIL, DEMO_ADMIN_PASSWORD).status_code == 303
    queue = client.get("/reviews")
    assert "Demo trip" in queue.text
    assert "Demo Employee" in queue.text
    decision = client.post(
        f"/requests/{request_id}/approve",
        data={"comment": "Approved for the demo"},
        follow_redirects=True,
    )
    assert decision.status_code == 200
    assert "Approved" in decision.text
    assert "Approved for the demo" in decision.text
    assert "Submitted" in decision.text
    assert _rows()[0].status == STATUS_APPROVED
    client.post("/logout", follow_redirects=False)

    assert _login_as(client, DEMO_EMPLOYEE_EMAIL, DEMO_EMPLOYEE_PASSWORD).status_code == 303
    after = client.get(f"/requests/{request_id}")
    assert "Approved" in after.text
    assert "Approved for the demo" in after.text
    assert 'data-testid="request-timeline"' in after.text
    assert 'data-testid="request-withdraw"' not in after.text
