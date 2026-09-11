from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.budget import BudgetCreate, BudgetRead
from app.services.budget_service import list_budgets, set_budget

router = APIRouter(prefix="/api/v1/budgets", tags=["budgets"])


@router.get("", response_model=list[BudgetRead])
def list_my_budgets(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[BudgetRead]:
    return list_budgets(db, current_user.id)


@router.post("", response_model=BudgetRead, status_code=status.HTTP_201_CREATED)
def set_my_budget(
    data: BudgetCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> BudgetRead:
    return set_budget(db, current_user.id, data.category_id, data.monthly_limit)
