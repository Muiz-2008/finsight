import uuid
from dataclasses import dataclass
from datetime import date as date_

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.models.transaction import Transaction, TransactionType


@dataclass(frozen=True)
class TransactionFilter:
    date_from: date_ | None = None
    date_to: date_ | None = None
    category_id: uuid.UUID | None = None
    account_id: uuid.UUID | None = None
    transaction_type: TransactionType | None = None


class TransactionRepository:
    """All filtering, sorting, and pagination happens in the SQL query, not
    in Python — a user with 500,000 transactions never has more than one
    page of rows pulled into memory. See app/analytics for the contrasting
    case (aggregation queries that *do* need the row-level data).
    """

    def __init__(self, db: Session) -> None:
        self._db = db

    def _base_query(self, user_id: uuid.UUID, filters: TransactionFilter):
        query = select(Transaction).where(Transaction.user_id == user_id)
        if filters.date_from is not None:
            query = query.where(Transaction.date >= filters.date_from)
        if filters.date_to is not None:
            query = query.where(Transaction.date <= filters.date_to)
        if filters.category_id is not None:
            query = query.where(Transaction.category_id == filters.category_id)
        if filters.account_id is not None:
            query = query.where(Transaction.account_id == filters.account_id)
        if filters.transaction_type is not None:
            query = query.where(Transaction.transaction_type == filters.transaction_type)
        return query

    def list_page(
        self,
        user_id: uuid.UUID,
        filters: TransactionFilter,
        limit: int,
        offset: int,
        sort_desc: bool = True,
    ) -> tuple[list[Transaction], int]:
        base = self._base_query(user_id, filters)

        total = self._db.scalar(select(func.count()).select_from(base.subquery())) or 0

        order_col = Transaction.date.desc() if sort_desc else Transaction.date.asc()
        paginated = (
            base.order_by(order_col, Transaction.created_at.desc()).limit(limit).offset(offset)
        )
        rows = self._db.execute(paginated).scalars().all()
        return list(rows), total

    def get(self, user_id: uuid.UUID, transaction_id: uuid.UUID) -> Transaction | None:
        return self._db.scalar(
            select(Transaction).where(
                Transaction.user_id == user_id, Transaction.id == transaction_id
            )
        )

    def create(self, transaction: Transaction) -> Transaction:
        self._db.add(transaction)
        self._db.commit()
        self._db.refresh(transaction)
        return transaction

    def delete(self, transaction: Transaction) -> None:
        self._db.delete(transaction)
        self._db.commit()

    def bulk_insert_ignore_duplicates(self, transactions: list[Transaction]) -> int:
        """Used by CSV import: one bulk INSERT with ON CONFLICT DO NOTHING
        against the (account_id, import_hash) unique constraint, instead of
        N individual inserts each wrapped in a try/except for
        IntegrityError. Returns how many rows were actually inserted (vs
        silently skipped as duplicates).
        """
        if not transactions:
            return 0

        rows = [
            {
                "id": t.id,
                "user_id": t.user_id,
                "account_id": t.account_id,
                "category_id": t.category_id,
                "amount": t.amount,
                "currency": t.currency,
                "transaction_type": t.transaction_type,
                "description": t.description,
                "date": t.date,
                "import_hash": t.import_hash,
            }
            for t in transactions
        ]
        stmt = pg_insert(Transaction).values(rows)
        stmt = stmt.on_conflict_do_nothing(
            index_elements=["account_id", "import_hash"]
        )
        result = self._db.execute(stmt)
        self._db.commit()
        return result.rowcount or 0
