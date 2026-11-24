from tests.test_leave_request import _form_token, _login, _register, _rows, _submit


def test_submitting_the_same_form_twice_creates_one_request(client):
    assert _register(client).status_code == 303
    assert _login(client).status_code == 303
    token = _form_token(client)

    first = _submit(client, form_token=token)
    second = _submit(client, form_token=token)

    assert first.status_code == 303
    assert first.headers["location"] == "/requests?saved=1"
    assert second.status_code == 303
    assert second.headers["location"] == "/requests?duplicate=1"
    assert len(_rows()) == 1

    listing = client.get("/requests?duplicate=1")
    assert 'data-testid="request-duplicate"' in listing.text
    assert listing.text.count('data-testid="request-row"') == 1


def test_a_new_form_can_still_create_another_request(client):
    assert _register(client).status_code == 303
    assert _login(client).status_code == 303
    assert _submit(client, reason="First trip").status_code == 303
    assert _submit(client, reason="Second trip").status_code == 303
    reasons = {row.reason for row in _rows()}
    assert reasons == {"First trip", "Second trip"}


def test_a_validation_error_keeps_the_form_token(client):
    assert _register(client).status_code == 303
    assert _login(client).status_code == 303
    token = _form_token(client)

    invalid = _submit(client, form_token=token, end_date="2001-06-01")
    assert invalid.status_code == 400
    assert token in invalid.text
    assert _rows() == []

    saved = _submit(client, form_token=token)
    assert saved.status_code == 303
    assert len(_rows()) == 1


def test_a_missing_form_token_does_not_create_a_request(client):
    assert _register(client).status_code == 303
    assert _login(client).status_code == 303
    response = _submit(client, form_token="")
    assert response.status_code == 400
    assert "submit it once" in response.text
    assert _rows() == []
