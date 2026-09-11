import uuid
from datetime import date as date_

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.ingestion.csv_importer import import_transactions_csv
from app.models.transaction import TransactionType
from app.models.user import User
from app.repositories.transaction_repository import TransactionFilter
from app.schemas.ingestion import ImportReportRead
from app.schemas.transaction import (
    TransactionCreate,
    TransactionPage,
    TransactionRead,
    TransactionUpdate,
)
from app.services import transaction_service
from app.services.account_service import get_owned_account

router = APIRouter(prefix="/api/v1/transactions", tags=["transactions"])

# Unbounded upload size is a real DoS vector (a client can stream an
# arbitrarily large "CSV" and exhaust memory/CPU parsing it) — capped well
# above any legitimate personal-finance export, generously enough that no
# real CSV a user has should ever hit it.
MAX_IMPORT_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


@router.post("/import", response_model=ImportReportRead)
async def import_transactions(
    account_id: uuid.UUID = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ImportReportRead:
    get_owned_account(db, current_user.id, account_id)  # 404s if not this user's account

    contents = await file.read(MAX_IMPORT_FILE_SIZE_BYTES + 1)
    if len(contents) > MAX_IMPORT_FILE_SIZE_BYTES:
        limit_mb = MAX_IMPORT_FILE_SIZE_BYTES // (1024 * 1024)
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds the {limit_mb}MB import limit.",
        )

    report = import_transactions_csv(db, current_user.id, account_id, contents)
    return ImportReportRead(**report.__dict__)


@router.get("", response_model=TransactionPage)
def list_my_transactions(
    date_from: date_ | None = None,
    date_to: date_ | None = None,
    category_id: uuid.UUID | None = None,
    account_id: uuid.UUID | None = None,
    transaction_type: TransactionType | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    sort_desc: bool = True,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TransactionPage:
    filters = TransactionFilter(
        date_from=date_from,
        date_to=date_to,
        category_id=category_id,
        account_id=account_id,
        transaction_type=transaction_type,
    )
    items, total = transaction_service.list_transactions(
        db, current_user.id, filters, limit, offset, sort_desc
    )
    return TransactionPage(items=items, total=total, limit=limit, offset=offset)


@router.post("", response_model=TransactionRead, status_code=status.HTTP_201_CREATED)
def create_my_transaction(
    data: TransactionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TransactionRead:
    return transaction_service.create_transaction(db, current_user.id, data)


@router.get("/{transaction_id}", response_model=TransactionRead)
def get_my_transaction(
    transaction_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TransactionRead:
    return transaction_service.get_owned_transaction(db, current_user.id, transaction_id)


@router.put("/{transaction_id}", response_model=TransactionRead)
def update_my_transaction(
    transaction_id: uuid.UUID,
    data: TransactionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TransactionRead:
    return transaction_service.update_transaction(db, current_user.id, transaction_id, data)


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_my_transaction(
    transaction_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    transaction_service.delete_transaction(db, current_user.id, transaction_id)
