from datetime import date

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_engine
from app.leave import LeaveRequestInput, LeaveStateError, create_leave_request
from app.models import User
from tests.test_leave_request import _login, _register, _rows, _submit


def test_form_still_rejects_an_end_date_before_the_start(client):
    assert _register(client).status_code == 303
    assert _login(client).status_code == 303

    response = _submit(client, start_date="2001-06-14", end_date="2001-06-12")

    assert response.status_code == 400
    assert "on or after the start date" in response.text
    assert _rows() == []


def test_save_path_rejects_an_end_date_before_the_start(client):
    assert _register(client).status_code == 303
    with Session(get_engine()) as db:
        user = db.scalars(select(User)).one()
        with pytest.raises(LeaveStateError) as caught:
            create_leave_request(
                db,
                user.id,
                LeaveRequestInput(date(2001, 6, 14), date(2001, 6, 12), "Backwards"),
            )
        assert "on or after the start date" in caught.value.message
    assert _rows() == []


def test_same_start_and_end_date_is_one_day(client):
    assert _register(client).status_code == 303
    assert _login(client).status_code == 303

    response = _submit(client, start_date="2001-06-12", end_date="2001-06-12", reason="One day")

    assert response.status_code == 303
    saved = _rows()
    assert len(saved) == 1
    assert saved[0].start_date == saved[0].end_date
