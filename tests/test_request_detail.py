from tests.test_leave_request import _login, _register, _rows, _submit


def test_request_detail_requires_sign_in(client):
    response = client.get("/requests/1", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_owner_can_open_request_details_from_the_list(client):
    assert _register(client).status_code == 303
    assert _login(client).status_code == 303
    assert _submit(client).status_code == 303

    listing = client.get("/requests")
    assert 'data-testid="request-detail-link"' in listing.text
    detail = client.get(f"/requests/{_rows()[0].id}")
    assert detail.status_code == 200
    assert 'data-testid="request-detail"' in detail.text
    assert 'data-testid="request-detail-dates"' in detail.text
    assert "2001-06-12 to 2001-06-14" in detail.text
    assert 'data-testid="request-detail-days"' in detail.text
    assert ">3<" in detail.text
    assert "Family visit" in detail.text
    assert "Pending" in detail.text
    assert 'data-testid="request-detail-submitted"' in detail.text
    assert 'data-testid="request-detail-back"' in detail.text


def test_another_user_cannot_open_the_request(client):
    assert _register(client).status_code == 303
    assert _login(client).status_code == 303
    assert _submit(client, reason="Ada private trip").status_code == 303
    request_id = _rows()[0].id
    client.post("/logout", follow_redirects=False)

    assert _register(client, email="grace@example.com", display_name="Grace Hopper").status_code == 303
    assert _login(client, email="grace@example.com").status_code == 303
    hidden = client.get(f"/requests/{request_id}")
    assert hidden.status_code == 404
    assert "Ada private trip" not in hidden.text
    assert 'data-testid="not-found"' in hidden.text


def test_missing_request_is_not_found(client):
    assert _register(client).status_code == 303
    assert _login(client).status_code == 303
    missing = client.get("/requests/999")
    assert missing.status_code == 404
    assert 'data-testid="not-found"' in missing.text
