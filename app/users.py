import re
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import ROLE_EMPLOYEE, User
from app.security import hash_password

_EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")


class DuplicateEmailError(Exception):
    pass


@dataclass(frozen=True)
class RegistrationInput:
    email: str
    display_name: str
    password: str


def validate_registration(
    email: str,
    display_name: str,
    password: str,
    password_confirm: str,
) -> tuple[RegistrationInput | None, list[str]]:
    errors: list[str] = []
    cleaned_email = email.strip().lower()
    cleaned_name = display_name.strip()

    if not cleaned_email or len(cleaned_email) > 254 or _EMAIL_RE.fullmatch(cleaned_email) is None:
        errors.append("Enter a valid email address.")
    if not cleaned_name or len(cleaned_name) > 80:
        errors.append("Display name must be between 1 and 80 characters.")
    elif any(ord(character) < 32 for character in cleaned_name):
        errors.append("Display name cannot include control characters.")
    if not 8 <= len(password) <= 128:
        errors.append("Password must be between 8 and 128 characters.")
    if password != password_confirm:
        errors.append("Password confirmation does not match.")

    if errors:
        return None, errors
    return RegistrationInput(cleaned_email, cleaned_name, password), []


def create_employee(db: Session, data: RegistrationInput) -> User:
    existing = db.scalar(select(User).where(User.email == data.email))
    if existing is not None:
        raise DuplicateEmailError
    user = User(
        email=data.email,
        display_name=data.display_name,
        password_hash=hash_password(data.password),
        role=ROLE_EMPLOYEE,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise DuplicateEmailError
    db.refresh(user)
    return user
