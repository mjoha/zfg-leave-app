from dataclasses import dataclass
from datetime import date

from sqlalchemy.orm import Session

from app.models import STATUS_PENDING, LeaveRequest


@dataclass(frozen=True)
class LeaveRequestInput:
    start_date: date
    end_date: date
    reason: str


def inclusive_days(start_date: date, end_date: date) -> int:
    return (end_date - start_date).days + 1


def _parse_date(value: str) -> date | None:
    try:
        return date.fromisoformat(value.strip())
    except ValueError:
        return None


def validate_leave_request(
    start_raw: str,
    end_raw: str,
    reason_raw: str,
) -> tuple[LeaveRequestInput | None, list[str]]:
    errors: list[str] = []
    start_date = _parse_date(start_raw)
    end_date = _parse_date(end_raw)
    if start_date is None:
        errors.append("Enter a start date as YYYY-MM-DD.")
    if end_date is None:
        errors.append("Enter an end date as YYYY-MM-DD.")
    if start_date is not None and end_date is not None and end_date < start_date:
        errors.append("End date must be on or after the start date.")

    reason = reason_raw.strip()
    if not reason or len(reason) > 500:
        errors.append("Reason must be between 1 and 500 characters.")
    elif any(ord(character) < 32 and character not in "\n\t" for character in reason):
        errors.append("Reason cannot include control characters.")

    if errors or start_date is None or end_date is None:
        return None, errors
    return LeaveRequestInput(start_date, end_date, reason), []


def create_leave_request(db: Session, user_id: int, data: LeaveRequestInput) -> LeaveRequest:
    row = LeaveRequest(
        user_id=user_id,
        start_date=data.start_date,
        end_date=data.end_date,
        reason=data.reason,
        status=STATUS_PENDING,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row
