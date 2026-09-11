import uuid

from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:
    """Query layer for User. Keeps raw SQLAlchemy queries out of the
    service layer, and is the single place that knows the User table's
    shape — services depend on this interface, not on ORM internals.
    """

    def __init__(self, db: Session) -> None:
        self._db = db

    def get_by_id(self, user_id: uuid.UUID) -> User | None:
        return self._db.get(User, user_id)

    def get_by_email(self, email: str) -> User | None:
        return self._db.query(User).filter(User.email == email).first()

    def create(self, *, email: str, hashed_password: str, full_name: str | None) -> User:
        user = User(email=email, hashed_password=hashed_password, full_name=full_name)
        self._db.add(user)
        self._db.commit()
        self._db.refresh(user)
        return user
