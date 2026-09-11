import uuid
from datetime import date as date_
from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.transaction import Transaction, TransactionType


class AnalyticsRepository:
    """Aggregation queries for the analytics engine. Every method here
    lets Postgres do the summing/grouping (GROUP BY, SUM, date_trunc)
    instead of pulling raw transaction rows into Python and reducing them
    with a loop — the same principle as pagination in
    TransactionRepository, applied to aggregates: a user with a million
    transactions still gets a handful of aggregate rows back, not a
    million-row fetch.
    """

    def __init__(self, db: Session) -> None:
        self._db = db

    def totals_by_type(
        self, user_id: uuid.UUID, date_from: date_, date_to: date_
    ) -> dict[TransactionType, Decimal]:
        rows = (
            self._db.query(Transaction.transaction_type, func.sum(Transaction.amount))
            .filter(
                Transaction.user_id == user_id,
                Transaction.date >= date_from,
                Transaction.date <= date_to,
            )
            .group_by(Transaction.transaction_type)
            .all()
        )
        return {t: total for t, total in rows}

    def totals_by_category(
        self, user_id: uuid.UUID, date_from: date_, date_to: date_
    ) -> list[tuple[str, Decimal]]:
        rows = (
            self._db.query(Category.name, func.sum(Transaction.amount))
            .join(Category, Transaction.category_id == Category.id)
            .filter(
                Transaction.user_id == user_id,
                Transaction.transaction_type == TransactionType.EXPENSE,
                Transaction.date >= date_from,
                Transaction.date <= date_to,
            )
            .group_by(Category.name)
            .order_by(func.sum(Transaction.amount).desc())
            .all()
        )
        return [(name, total) for name, total in rows]

    def monthly_totals(
        self, user_id: uuid.UUID, date_from: date_, date_to: date_
    ) -> list[tuple[date_, TransactionType, Decimal]]:
        month = func.date_trunc("month", Transaction.date)
        rows = (
            self._db.query(month, Transaction.transaction_type, func.sum(Transaction.amount))
            .filter(
                Transaction.user_id == user_id,
                Transaction.date >= date_from,
                Transaction.date <= date_to,
            )
            .group_by(month, Transaction.transaction_type)
            .order_by(month)
            .all()
        )
        return [(m.date(), t, total) for m, t, total in rows]

    def top_transactions(
        self, user_id: uuid.UUID, date_from: date_, date_to: date_, limit: int
    ) -> list[Transaction]:
        return (
            self._db.query(Transaction)
            .filter(
                Transaction.user_id == user_id,
                Transaction.date >= date_from,
                Transaction.date <= date_to,
            )
            .order_by(Transaction.amount.desc())
            .limit(limit)
            .all()
        )
