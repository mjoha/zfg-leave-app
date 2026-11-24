from tests.test_leave_request import _login, _register, _submit


def test_week_shows_seven_days_and_the_users_requests(client):
    assert _register(client).status_code == 303
    assert _login(client).status_code == 303
    assert _submit(client, start_date="2001-06-12", end_date="2001-06-14", reason="Mid week").status_code == 303
    assert _submit(client, start_date="2001-06-30", end_date="2001-06-30", reason="Month edge").status_code == 303

    page = client.get("/calendar/week?day=2001-06-12")
    assert page.status_code == 200
    assert 'data-testid="calendar-week"' in page.text
    assert page.text.count('data-testid="calendar-day"') == 7
    assert 'data-date="2001-06-11"' in page.text
    assert 'data-date="2001-06-17"' in page.text
    assert page.text.count("Mid week") == 3
    assert "Month edge" not in page.text

    edge = client.get("/calendar/week?day=2001-06-30")
    assert 'data-date="2001-06-30"' in edge.text
    assert "Month edge" in edge.text


def test_month_page_links_to_the_week(client):
    assert _register(client).status_code == 303
    assert _login(client).status_code == 303
    page = client.get("/calendar?year=2001&month=6")
    assert 'href="/calendar/week?day=2001-06-01"' in page.text


def test_invalid_week_date_is_rejected(client):
    assert _register(client).status_code == 303
    assert _login(client).status_code == 303
    response = client.get("/calendar/week?day=June")
    assert response.status_code == 400
    assert 'data-testid="calendar-error"' in response.text


def test_week_requires_sign_in(client):
    response = client.get("/calendar/week", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/login"
