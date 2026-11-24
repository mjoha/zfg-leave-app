from app.models import STATUS_PENDING
from app.seed import (
    DEMO_ADMIN_EMAIL,
    DEMO_ADMIN_PASSWORD,
    DEMO_EMPLOYEE_EMAIL,
    DEMO_EMPLOYEE_PASSWORD,
    seed_database,
)
from tests.test_leave_request import _login, _register, _rows, _submit


def _login_as(client, email: str, password: str):
    return client.post(
        "/login",
        data={"email": email, "password": password},
        follow_redirects=False,
    )


def test_review_queue_requires_sign_in(client):
    response = client.get("/reviews", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_employee_cannot_open_the_review_queue(client):
    seed_database()
    assert _login_as(client, DEMO_EMPLOYEE_EMAIL, DEMO_EMPLOYEE_PASSWORD).status_code == 303
    home = client.get("/")
    assert 'data-testid="nav-review"' not in home.text
    response = client.get("/reviews")
    assert response.status_code == 403
    assert 'data-testid="review-forbidden"' in response.text
    assert "Demo trip" not in response.text


def test_administrator_sees_pending_requests_and_can_open_them(client):
    seed_database()
    assert _login_as(client, DEMO_ADMIN_EMAIL, DEMO_ADMIN_PASSWORD).status_code == 303
    queue = client.get("/reviews")
    assert queue.status_code == 200
    assert 'data-testid="nav-review"' in queue.text
    assert 'data-testid="review-queue"' in queue.text
    assert queue.text.count('data-testid="review-row"') == 1
    assert "Demo Employee" in queue.text
    assert "Demo trip" in queue.text
    assert "2001-06-12 to 2001-06-14" in queue.text

    request_id = _rows()[0].id
    detail = client.get(f"/requests/{request_id}")
    assert detail.status_code == 200
    assert "Demo trip" in detail.text
    assert 'data-testid="request-withdraw"' not in detail.text
    assert 'data-testid="review-back"' in detail.text
    assert _rows()[0].status == STATUS_PENDING


def test_withdrawn_requests_leave_the_queue(client):
    assert _register(client).status_code == 303
    assert _login(client).status_code == 303
    assert _submit(client, reason="Soon withdrawn").status_code == 303
    request_id = _rows()[0].id
    assert client.post(f"/requests/{request_id}/withdraw", follow_redirects=False).status_code == 303
    client.post("/logout", follow_redirects=False)

    seed_database()
    assert _login_as(client, DEMO_ADMIN_EMAIL, DEMO_ADMIN_PASSWORD).status_code == 303
    queue = client.get("/reviews")
    assert "Soon withdrawn" not in queue.text
    assert "Demo trip" in queue.text


def test_employee_still_cannot_open_another_employees_request(client):
    seed_database()
    request_id = _rows()[0].id
    assert _register(client, email="grace@example.com", display_name="Grace Hopper").status_code == 303
    assert _login(client, email="grace@example.com").status_code == 303
    hidden = client.get(f"/requests/{request_id}")
    assert hidden.status_code == 404
    assert "Demo trip" not in hidden.text
