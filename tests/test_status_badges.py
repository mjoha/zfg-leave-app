from app.seed import DEMO_ADMIN_EMAIL, DEMO_ADMIN_PASSWORD, seed_database
from tests.test_leave_request import _login, _register, _rows, _submit
from tests.test_review_queue import _login_as


def test_pending_approved_rejected_and_withdrawn_use_colored_badges(client):
    assert _register(client).status_code == 303
    assert _login(client).status_code == 303
    assert _submit(client, reason="Pending trip").status_code == 303
    pending = client.get("/requests")
    assert 'class="status-badge status-pending"' in pending.text
    assert 'data-testid="request-status"' in pending.text

    request_id = _rows()[0].id
    client.post("/logout", follow_redirects=False)
    seed_database()
    assert _login_as(client, DEMO_ADMIN_EMAIL, DEMO_ADMIN_PASSWORD).status_code == 303
    approved = client.post(f"/requests/{request_id}/approve", follow_redirects=True)
    assert 'class="status-badge status-approved"' in approved.text

    assert _register(client, email="grace@example.com", display_name="Grace Hopper").status_code == 303
    assert _login(client, email="grace@example.com").status_code == 303
    assert _submit(client, reason="Reject me").status_code == 303
    rejected_id = [row.id for row in _rows() if row.reason == "Reject me"][0]
    client.post("/logout", follow_redirects=False)
    assert _login_as(client, DEMO_ADMIN_EMAIL, DEMO_ADMIN_PASSWORD).status_code == 303
    rejected = client.post(f"/requests/{rejected_id}/reject", follow_redirects=True)
    assert 'class="status-badge status-rejected"' in rejected.text

    assert _login(client, email="grace@example.com").status_code == 303
    assert _submit(client, reason="Withdraw me").status_code == 303
    withdrawn_id = [row.id for row in _rows() if row.reason == "Withdraw me"][0]
    withdrawn = client.post(f"/requests/{withdrawn_id}/withdraw", follow_redirects=True)
    assert 'class="status-badge status-withdrawn"' in withdrawn.text
    queue = client.get("/reviews")
    assert "status-pending" in queue.text or 'data-testid="review-forbidden"' in queue.text
