from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.account import AccountCreate, AccountRead
from app.services.account_service import create_account, list_accounts

router = APIRouter(prefix="/api/v1/accounts", tags=["accounts"])


@router.get("", response_model=list[AccountRead])
def list_my_accounts(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[AccountRead]:
    return list_accounts(db, current_user.id)


@router.post("", response_model=AccountRead, status_code=status.HTTP_201_CREATED)
def create_my_account(
    data: AccountCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AccountRead:
    return create_account(db, current_user.id, data.name, data.account_type, data.currency)
