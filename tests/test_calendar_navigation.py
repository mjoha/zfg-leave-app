from datetime import date

from tests.test_leave_request import _login, _register


def test_month_navigation_moves_one_month_and_marks_today(client, monkeypatch):
    monkeypatch.setattr("app.main._today", lambda: date(2001, 6, 12))
    assert _register(client).status_code == 303
    assert _login(client).status_code == 303

    page = client.get("/calendar?year=2001&month=6")
    assert 'href="/calendar?year=2001&amp;month=5"' in page.text or 'href="/calendar?year=2001&month=5"' in page.text
    assert "month=7" in page.text
    assert 'data-testid="calendar-today"' in page.text
    assert 'href="/calendar?year=2001&amp;month=6"' in page.text or 'href="/calendar?year=2001&month=6"' in page.text
    assert 'data-date="2001-06-12"' in page.text
    assert 'data-testid="calendar-today-marker"' in page.text
    assert page.text.find('data-date="2001-06-12"') < page.text.find('data-testid="calendar-today-marker"')

    other = client.get("/calendar?year=2001&month=5")
    assert 'data-testid="calendar-today-marker"' not in other.text


def test_week_navigation_moves_seven_days(client, monkeypatch):
    monkeypatch.setattr("app.main._today", lambda: date(2001, 6, 12))
    assert _register(client).status_code == 303
    assert _login(client).status_code == 303
    page = client.get("/calendar/week?day=2001-06-12")
    assert "2001-06-04" in page.text
    assert "2001-06-18" in page.text
    assert 'href="/calendar/week?day=2001-06-12"' in page.text
    assert 'data-testid="calendar-today-marker"' in page.text
