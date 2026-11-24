from tests.test_leave_request import _form_token, _login, _register, _rows


def _preview(client, token: str, **overrides):
    payload = {
        "start_date": "2001-06-12",
        "end_date": "2001-06-14",
        "reason": "Family visit",
        "form_token": token,
    }
    payload.update(overrides)
    return client.post("/requests", data=payload, follow_redirects=False)


def test_valid_request_asks_for_confirmation_before_saving(client):
    assert _register(client).status_code == 303
    assert _login(client).status_code == 303
    token = _form_token(client)
    preview = _preview(client, token)
    assert preview.status_code == 200
    assert 'data-testid="request-confirm"' in preview.text
    assert "2001-06-12 to 2001-06-14" in preview.text
    assert "Family visit" in preview.text
    assert ">3<" in preview.text
    assert _rows() == []

    saved = client.post("/requests/confirm", follow_redirects=False)
    assert saved.status_code == 303
    assert saved.headers["location"] == "/requests?saved=1"
    assert len(_rows()) == 1
    assert _rows()[0].reason == "Family visit"


def test_confirming_twice_does_not_create_a_second_request(client):
    assert _register(client).status_code == 303
    assert _login(client).status_code == 303
    token = _form_token(client)
    assert _preview(client, token).status_code == 200
    assert client.post("/requests/confirm", follow_redirects=False).status_code == 303
    again = client.post("/requests/confirm", follow_redirects=False)
    assert again.status_code == 303
    assert again.headers["location"] == "/requests/new"
    assert len(_rows()) == 1


def test_leaving_the_confirmation_does_not_save(client):
    assert _register(client).status_code == 303
    assert _login(client).status_code == 303
    token = _form_token(client)
    assert _preview(client, token).status_code == 200
    cancelled = client.get("/requests/new")
    assert cancelled.status_code == 200
    assert _rows() == []
