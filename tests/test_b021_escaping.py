from app.seed import DEMO_ADMIN_EMAIL, DEMO_ADMIN_PASSWORD, seed_database
from tests.test_leave_request import _form_token, _login, _register, _rows
from tests.test_review_queue import _login_as, decision_payload

REASON = 'Trip <img src="x" onerror="alert(1)">'
COMMENT = "<script>alert(1)</script>"


def test_request_text_is_escaped_on_the_pages_that_show_it(client):
    assert _register(client).status_code == 303
    assert _login(client).status_code == 303
    token = _form_token(client)
    preview = client.post(
        "/requests",
        data={
            "start_date": "2001-06-12",
            "end_date": "2001-06-12",
            "reason": REASON,
            "form_token": token,
        },
    )
    assert preview.status_code == 200
    assert REASON not in preview.text
    assert "Trip &lt;img" in preview.text

    assert client.post("/requests/confirm", follow_redirects=False).status_code == 303
    request_id = _rows()[0].id
    listing = client.get("/requests")
    detail = client.get(f"/requests/{request_id}")
    calendar = client.get("/calendar?year=2001&month=6")
    for page in (listing, detail, calendar):
        assert REASON not in page.text
        assert "Trip &lt;img" in page.text

    client.post("/logout", follow_redirects=False)
    seed_database()
    assert _login_as(client, DEMO_ADMIN_EMAIL, DEMO_ADMIN_PASSWORD).status_code == 303
    decided = client.post(
        f"/requests/{request_id}/approve",
        data=decision_payload(client, request_id, comment=COMMENT, expected_status="pending"),
        follow_redirects=True,
    )
    assert COMMENT not in decided.text
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in decided.text
    assert _rows()[0].decision_comment == COMMENT
