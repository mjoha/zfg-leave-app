"""Queries for the administrator review queue."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import STATUS_PENDING, LeaveRequest, User


def list_pending_reviews(db: Session) -> list[tuple[LeaveRequest, str]]:
    statement = (
        select(LeaveRequest, User.display_name)
        .join(User, User.id == LeaveRequest.user_id)
        .where(LeaveRequest.status == STATUS_PENDING)
        .order_by(LeaveRequest.created_at.asc(), LeaveRequest.id.asc())
    )
    return [(row, name) for row, name in db.execute(statement).all()]
