from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.category import CategoryCreate, CategoryRead
from app.services.category_service import create_category, list_categories

router = APIRouter(prefix="/api/v1/categories", tags=["categories"])


@router.get("", response_model=list[CategoryRead])
def list_my_categories(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[CategoryRead]:
    return list_categories(db, current_user.id)


@router.post("", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
def create_my_category(
    data: CategoryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CategoryRead:
    return create_category(db, current_user.id, data.name)
