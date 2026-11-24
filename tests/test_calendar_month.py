from tests.test_leave_request import _login, _register, _submit


def test_calendar_requires_sign_in(client):
    response = client.get("/calendar", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_month_shows_the_users_requests_and_omits_the_final_day(client):
    assert _register(client).status_code == 303
    assert _login(client).status_code == 303
    assert _submit(client, start_date="2001-06-12", end_date="2001-06-14", reason="Mid month").status_code == 303
    assert _submit(client, start_date="2001-06-01", end_date="2001-06-01", reason="First day").status_code == 303
    assert _submit(client, start_date="2001-06-30", end_date="2001-06-30", reason="Last day").status_code == 303

    page = client.get("/calendar?year=2001&month=6")
    assert page.status_code == 200
    assert 'data-testid="calendar-title"' in page.text
    assert "June 2001" in page.text
    assert 'data-testid="nav-calendar"' in page.text
    assert 'data-date="2001-06-01"' in page.text
    assert 'data-date="2001-06-12"' in page.text
    assert 'data-date="2001-06-29"' in page.text
    assert 'data-date="2001-06-30"' not in page.text
    assert page.text.count("Mid month") == 3
    assert "First day" in page.text
    assert "Last day" not in page.text


def test_calendar_hides_another_users_requests(client):
    assert _register(client).status_code == 303
    assert _login(client).status_code == 303
    assert _submit(client, start_date="2001-06-12", end_date="2001-06-12", reason="Ada private trip").status_code == 303
    client.post("/logout", follow_redirects=False)
    assert _register(client, email="grace@example.com", display_name="Grace Hopper").status_code == 303
    assert _login(client, email="grace@example.com").status_code == 303
    page = client.get("/calendar?year=2001&month=6")
    assert "Ada private trip" not in page.text


def test_invalid_month_is_rejected(client):
    assert _register(client).status_code == 303
    assert _login(client).status_code == 303
    response = client.get("/calendar?year=2001&month=13")
    assert response.status_code == 400
    assert 'data-testid="calendar-error"' in response.text
