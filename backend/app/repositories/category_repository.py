import uuid

from sqlalchemy.orm import Session

from app.models.category import Category

DEFAULT_CATEGORIES = [
    "Income",
    "Groceries",
    "Transport",
    "Housing",
    "Utilities",
    "Entertainment",
    "Healthcare",
    "Dining",
    "Shopping",
    "Other",
]


class CategoryRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def list_for_user(self, user_id: uuid.UUID) -> list[Category]:
        return (
            self._db.query(Category)
            .filter(Category.user_id == user_id)
            .order_by(Category.name)
            .all()
        )

    def get(self, user_id: uuid.UUID, category_id: uuid.UUID) -> Category | None:
        return (
            self._db.query(Category)
            .filter(Category.user_id == user_id, Category.id == category_id)
            .first()
        )

    def create(self, user_id: uuid.UUID, name: str) -> Category:
        category = Category(user_id=user_id, name=name)
        self._db.add(category)
        self._db.commit()
        self._db.refresh(category)
        return category

    def seed_defaults(self, user_id: uuid.UUID) -> None:
        """Give a new user a starter taxonomy instead of an empty list —
        they can rename/delete/add to it, but nobody starts from zero.
        """
        for name in DEFAULT_CATEGORIES:
            self._db.add(Category(user_id=user_id, name=name))
        self._db.commit()
