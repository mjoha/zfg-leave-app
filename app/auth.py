"""Session lookup for signed-in pages. The cookie stores only a user id."""

import secrets

from fastapi import Request
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.database import get_engine
from app.models import User


def establish_session(request: Request, user_id: int) -> None:
    request.session.clear()
    request.session["user_id"] = user_id


def clear_session(request: Request) -> None:
    request.session.clear()


def issue_csrf(request: Request) -> str:
    token = request.session.get("csrf_token")
    if not isinstance(token, str) or len(token) < 16:
        token = secrets.token_urlsafe(32)
        request.session["csrf_token"] = token
    return token


def csrf_matches(request: Request, posted: str) -> bool:
    expected = request.session.get("csrf_token")
    return isinstance(expected, str) and bool(posted) and posted == expected


def signed_in_user(request: Request) -> User | None:
    user_id = request.session.get("user_id")
    if not isinstance(user_id, int):
        return None
    db = Session(get_engine())
    try:
        user = db.get(User, user_id)
        if user is None:
            request.session.pop("user_id", None)
            return None
        db.expunge(user)
        return user
    except OperationalError:
        return None
    finally:
        db.close()


def load_session_user(request: Request, db: Session) -> User | None:
    user_id = request.session.get("user_id")
    if not isinstance(user_id, int):
        return None
    user = db.get(User, user_id)
    if user is None:
        request.session.pop("user_id", None)
    return user
