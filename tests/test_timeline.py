from app.models import STATUS_WITHDRAWN
from app.seed import DEMO_ADMIN_EMAIL, DEMO_ADMIN_PASSWORD, seed_database
from tests.test_leave_request import _login, _register, _rows, _submit
from tests.test_review_queue import _login_as, decision_payload


def _labels(body: str) -> list[str]:
    marker = 'data-testid="request-timeline-label">'
    labels = []
    start = 0
    while True:
        found = body.find(marker, start)
        if found < 0:
            return labels
        value_start = found + len(marker)
        value_end = body.find("</span>", value_start)
        labels.append(body[value_start:value_end])
        start = value_end


def test_pending_request_timeline_has_only_submission(client):
    assert _register(client).status_code == 303
    assert _login(client).status_code == 303
    assert _submit(client).status_code == 303
    detail = client.get(f"/requests/{_rows()[0].id}")
    assert 'data-testid="request-timeline"' in detail.text
    assert _labels(detail.text) == ["Submitted"]
    assert detail.text.count('data-testid="request-timeline-when"') == 1


def test_decision_appends_a_timeline_event_with_the_comment(client):
    seed_database()
    request_id = _rows()[0].id
    assert _login_as(client, DEMO_ADMIN_EMAIL, DEMO_ADMIN_PASSWORD).status_code == 303
    assert client.post(
        f"/requests/{request_id}/approve",
        data=decision_payload(client, request_id, comment="See you then"),
        follow_redirects=False,
    ).status_code == 303
    detail = client.get(f"/requests/{request_id}")
    assert _labels(detail.text) == ["Submitted", "Approved"]
    assert detail.text.count('data-testid="request-timeline-when"') == 2
    assert "See you then" in detail.text
    submitted_at = detail.text.find(">Submitted<")
    approved_at = detail.text.find(">Approved<")
    assert submitted_at < approved_at


def test_withdrawal_appends_a_timed_timeline_event(client):
    assert _register(client).status_code == 303
    assert _login(client).status_code == 303
    assert _submit(client).status_code == 303
    request_id = _rows()[0].id
    assert client.post(f"/requests/{request_id}/withdraw", follow_redirects=False).status_code == 303
    saved = _rows()[0]
    assert saved.status == STATUS_WITHDRAWN
    assert saved.decided_at is not None
    detail = client.get(f"/requests/{request_id}")
    assert _labels(detail.text) == ["Submitted", "Withdrawn"]
    assert detail.text.count('data-testid="request-timeline-when"') == 2
