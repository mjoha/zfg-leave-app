from dataclasses import dataclass
from datetime import date

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import (
    ROLE_ADMINISTRATOR,
    STATUS_APPROVED,
    STATUS_PENDING,
    STATUS_REJECTED,
    STATUS_WITHDRAWN,
    LeaveRequest,
    SubmissionToken,
    User,
    utcnow,
)
from app.validation import ErrorList


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
    errors = ErrorList()
    start_date = _parse_date(start_raw)
    end_date = _parse_date(end_raw)
    if start_date is None:
        errors.add("Enter a start date as YYYY-MM-DD.")
    if end_date is None:
        errors.add("Enter an end date as YYYY-MM-DD.")
    if start_date is not None and end_date is not None and end_date < start_date:
        errors.add("End date must be on or after the start date.")

    reason = reason_raw.strip()
    if not reason or len(reason) > 500:
        errors.add("Reason must be between 1 and 500 characters.")
    elif any(ord(character) < 32 and character not in "\n\t" for character in reason):
        errors.add("Reason cannot include control characters.")

    if errors or start_date is None or end_date is None:
        return None, errors.messages()
    return LeaveRequestInput(start_date, end_date, reason), []


class LeaveStateError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


def status_label(status: str) -> str:
    labels = {
        STATUS_PENDING: "Pending",
        STATUS_WITHDRAWN: "Withdrawn",
        STATUS_APPROVED: "Approved",
        STATUS_REJECTED: "Rejected",
    }
    return labels.get(status, status)


def validate_decision_comment(comment_raw: str) -> tuple[str | None, list[str]]:
    errors = ErrorList()
    comment = comment_raw.strip()
    if not comment:
        return None, []
    if len(comment) > 500:
        errors.add("Comment must be 500 characters or fewer.")
    elif any(ord(character) < 32 and character not in "\n\t" for character in comment):
        errors.add("Comment cannot include control characters.")
    if errors:
        return None, errors.messages()
    return comment, []


def decide_leave_request(
    db: Session,
    row: LeaveRequest,
    status: str,
    comment: str | None,
) -> LeaveRequest:
    if status not in {STATUS_APPROVED, STATUS_REJECTED}:
        raise LeaveStateError("Choose approve or reject.")
    if row.status != STATUS_PENDING:
        raise LeaveStateError("Only a pending request can be decided.")
    row.status = status
    row.decision_comment = comment
    row.decided_at = utcnow()
    db.commit()
    db.refresh(row)
    return row


def withdraw_leave_request(db: Session, row: LeaveRequest) -> LeaveRequest:
    if row.status != STATUS_PENDING:
        raise LeaveStateError("Only a pending request can be withdrawn.")
    row.status = STATUS_WITHDRAWN
    row.decided_at = utcnow()
    db.commit()
    db.refresh(row)
    return row


def get_leave_request(db: Session, request_id: int) -> LeaveRequest | None:
    return db.get(LeaveRequest, request_id)


def can_view_leave_request(user: User, row: LeaveRequest) -> bool:
    return row.user_id == user.id or user.role == ROLE_ADMINISTRATOR


def list_pending_reviews(db: Session) -> list[tuple[LeaveRequest, str]]:
    statement = (
        select(LeaveRequest, User.display_name)
        .join(User, User.id == LeaveRequest.user_id)
        .where(LeaveRequest.status == STATUS_PENDING)
        .order_by(LeaveRequest.created_at.asc(), LeaveRequest.id.asc())
    )
    return [(row, name) for row, name in db.execute(statement).all()]


def list_leave_requests_for_user(db: Session, user_id: int) -> list[LeaveRequest]:
    statement = (
        select(LeaveRequest)
        .where(LeaveRequest.user_id == user_id)
        .order_by(LeaveRequest.created_at.desc(), LeaveRequest.id.desc())
    )
    return list(db.scalars(statement))


def create_leave_request(db: Session, user_id: int, data: LeaveRequestInput) -> LeaveRequest:
    if data.end_date < data.start_date:
        raise LeaveStateError("End date must be on or after the start date.")
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


def submission_token_used(db: Session, token: str) -> bool:
    return db.get(SubmissionToken, token) is not None


def create_leave_request_once(
    db: Session,
    user_id: int,
    data: LeaveRequestInput,
    token: str,
) -> LeaveRequest | None:
    """Save a request for a form token. A repeated token does not create another row."""
    if data.end_date < data.start_date:
        raise LeaveStateError("End date must be on or after the start date.")
    row = LeaveRequest(
        user_id=user_id,
        start_date=data.start_date,
        end_date=data.end_date,
        reason=data.reason,
        status=STATUS_PENDING,
    )
    db.add(row)
    db.flush()
    db.add(SubmissionToken(token=token, leave_request_id=row.id))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return None
    db.refresh(row)
    return row
