from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate
from app.security.hashing import hash_password, verify_password


class EmailAlreadyRegisteredError(Exception):
    pass


class InvalidCredentialsError(Exception):
    pass


def register_user(db: Session, user_in: UserCreate) -> User:
    repo = UserRepository(db)
    if repo.get_by_email(user_in.email) is not None:
        raise EmailAlreadyRegisteredError(user_in.email)

    return repo.create(
        email=user_in.email,
        hashed_password=hash_password(user_in.password),
        full_name=user_in.full_name,
    )


def authenticate_user(db: Session, email: str, password: str) -> User:
    """Look up the user and verify the password in one step.

    Deliberately raises the *same* error for "no such user" and "wrong
    password" — telling an attacker which one it was leaks whether an
    email address has an account, which is itself sensitive information.
    """
    repo = UserRepository(db)
    user = repo.get_by_email(email)
    if user is None or not verify_password(password, user.hashed_password):
        raise InvalidCredentialsError()
    return user
