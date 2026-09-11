import uuid

from sqlalchemy.orm import Session

from app.ingestion.dedup import compute_import_hash
from app.models.transaction import Transaction
from app.repositories.category_repository import CategoryRepository
from app.repositories.transaction_repository import TransactionFilter, TransactionRepository
from app.schemas.transaction import TransactionCreate, TransactionUpdate
from app.services.account_service import get_owned_account
from app.services.exceptions import NotFoundError, ValidationError


def list_transactions(
    db: Session,
    user_id: uuid.UUID,
    filters: TransactionFilter,
    limit: int,
    offset: int,
    sort_desc: bool = True,
) -> tuple[list[Transaction], int]:
    return TransactionRepository(db).list_page(user_id, filters, limit, offset, sort_desc)


def create_transaction(db: Session, user_id: uuid.UUID, data: TransactionCreate) -> Transaction:
    # Ownership checks happen here, not relying on a DB foreign key alone:
    # an FK only proves the account/category *exist*, not that they belong
    # to this user — without this check, User A could attach a transaction
    # to User B's account_id.
    get_owned_account(db, user_id, data.account_id)
    if data.category_id is not None:
        category = CategoryRepository(db).get(user_id, data.category_id)
        if category is None:
            raise ValidationError(f"category {data.category_id} not found")

    transaction = Transaction(
        id=uuid.uuid4(),
        user_id=user_id,
        account_id=data.account_id,
        category_id=data.category_id,
        amount=data.amount,
        currency=data.currency,
        transaction_type=data.transaction_type,
        description=data.description,
        date=data.date,
        import_hash=compute_import_hash(
            data.account_id, data.date, data.description, data.amount, data.transaction_type
        ),
    )
    return TransactionRepository(db).create(transaction)


def get_owned_transaction(
    db: Session, user_id: uuid.UUID, transaction_id: uuid.UUID
) -> Transaction:
    transaction = TransactionRepository(db).get(user_id, transaction_id)
    if transaction is None:
        raise NotFoundError(f"transaction {transaction_id} not found")
    return transaction


def update_transaction(
    db: Session, user_id: uuid.UUID, transaction_id: uuid.UUID, data: TransactionUpdate
) -> Transaction:
    transaction = get_owned_transaction(db, user_id, transaction_id)

    if data.category_id is not None:
        category = CategoryRepository(db).get(user_id, data.category_id)
        if category is None:
            raise ValidationError(f"category {data.category_id} not found")
        transaction.category_id = data.category_id
    if data.amount is not None:
        transaction.amount = data.amount
    if data.description is not None:
        transaction.description = data.description
    if data.date is not None:
        transaction.date = data.date

    transaction.import_hash = compute_import_hash(
        transaction.account_id,
        transaction.date,
        transaction.description,
        transaction.amount,
        transaction.transaction_type,
    )

    db.commit()
    db.refresh(transaction)
    return transaction


def delete_transaction(db: Session, user_id: uuid.UUID, transaction_id: uuid.UUID) -> None:
    transaction = get_owned_transaction(db, user_id, transaction_id)
    TransactionRepository(db).delete(transaction)
