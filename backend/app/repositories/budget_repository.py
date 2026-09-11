import uuid
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.budget import Budget


class BudgetRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def list_for_user(self, user_id: uuid.UUID) -> list[Budget]:
        return self._db.query(Budget).filter(Budget.user_id == user_id).all()

    def get_by_category(self, user_id: uuid.UUID, category_id: uuid.UUID) -> Budget | None:
        return (
            self._db.query(Budget)
            .filter(Budget.user_id == user_id, Budget.category_id == category_id)
            .first()
        )

    def upsert(self, user_id: uuid.UUID, category_id: uuid.UUID, monthly_limit: Decimal) -> Budget:
        existing = self.get_by_category(user_id, category_id)
        if existing is not None:
            existing.monthly_limit = monthly_limit
            self._db.commit()
            self._db.refresh(existing)
            return existing

        budget = Budget(user_id=user_id, category_id=category_id, monthly_limit=monthly_limit)
        self._db.add(budget)
        self._db.commit()
        self._db.refresh(budget)
        return budget
