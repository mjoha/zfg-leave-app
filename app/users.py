import re
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import ROLE_ADMINISTRATOR, ROLE_EMPLOYEE, User
from app.security import hash_password, verify_password

_DUMMY_PASSWORD_HASH: str | None = None

_EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")


class DuplicateEmailError(Exception):
    pass


@dataclass(frozen=True)
class RegistrationInput:
    email: str
    display_name: str
    password: str


def validate_display_name(display_name: str) -> tuple[str | None, list[str]]:
    cleaned = display_name.strip()
    if not cleaned or len(cleaned) > 80:
        return None, ["Display name must be between 1 and 80 characters."]
    if any(ord(character) < 32 for character in cleaned):
        return None, ["Display name cannot include control characters."]
    return cleaned, []


def role_label(role: str) -> str:
    labels = {
        ROLE_EMPLOYEE: "Employee",
        ROLE_ADMINISTRATOR: "Administrator",
    }
    return labels.get(role, role)


def validate_registration(
    email: str,
    display_name: str,
    password: str,
    password_confirm: str,
) -> tuple[RegistrationInput | None, list[str]]:
    errors: list[str] = []
    cleaned_email = email.strip().lower()
    cleaned_name, name_errors = validate_display_name(display_name)
    errors.extend(name_errors)

    if not cleaned_email or len(cleaned_email) > 254 or _EMAIL_RE.fullmatch(cleaned_email) is None:
        errors.append("Enter a valid email address.")
    if not 8 <= len(password) <= 128:
        errors.append("Password must be between 8 and 128 characters.")
    if password != password_confirm:
        errors.append("Password confirmation does not match.")

    if errors or cleaned_name is None:
        return None, errors
    return RegistrationInput(cleaned_email, cleaned_name, password), []


def _dummy_password_hash() -> str:
    global _DUMMY_PASSWORD_HASH
    if _DUMMY_PASSWORD_HASH is None:
        _DUMMY_PASSWORD_HASH = hash_password("local-timing-placeholder")
    return _DUMMY_PASSWORD_HASH


def authenticate(db: Session, email: str, password: str) -> User | None:
    cleaned = email.strip().lower()
    user = db.scalar(select(User).where(User.email == cleaned))
    if user is None:
        verify_password(password, _dummy_password_hash())
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


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
