import uuid
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.budget import Budget
from app.repositories.budget_repository import BudgetRepository
from app.repositories.category_repository import CategoryRepository
from app.services.exceptions import ValidationError


def list_budgets(db: Session, user_id: uuid.UUID) -> list[Budget]:
    return BudgetRepository(db).list_for_user(user_id)


def set_budget(
    db: Session, user_id: uuid.UUID, category_id: uuid.UUID, monthly_limit: Decimal
) -> Budget:
    if CategoryRepository(db).get(user_id, category_id) is None:
        raise ValidationError(f"category {category_id} not found")
    return BudgetRepository(db).upsert(user_id, category_id, monthly_limit)
