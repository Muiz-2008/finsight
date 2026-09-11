import uuid
from datetime import date as date_
from datetime import timedelta

from sqlalchemy.orm import Session

from app.analytics.anomaly import iqr_anomalies, zscore_anomalies
from app.models.category import Category
from app.models.transaction import Transaction, TransactionType
from app.schemas.anomaly import AnomalyRead
from app.schemas.transaction import TransactionRead

_DETECTORS = {"zscore": zscore_anomalies, "iqr": iqr_anomalies}


def detect_spending_anomalies(
    db: Session, user_id: uuid.UUID, method: str = "zscore", lookback_days: int = 180
) -> list[AnomalyRead]:
    """Flags unusual expense transactions *within each category*
    separately — comparing a $1,200 rent payment to a $15 coffee on one
    shared scale would flag rent every month for being large, which isn't
    useful. Each category has its own notion of "normal".
    """
    detector = _DETECTORS.get(method)
    if detector is None:
        raise ValueError(f"unknown method {method!r}; expected one of {list(_DETECTORS)}")

    since = date_.today() - timedelta(days=lookback_days)
    transactions = (
        db.query(Transaction, Category.name)
        .join(Category, Transaction.category_id == Category.id)
        .filter(
            Transaction.user_id == user_id,
            Transaction.transaction_type == TransactionType.EXPENSE,
            Transaction.date >= since,
        )
        .order_by(Transaction.category_id, Transaction.date)
        .all()
    )

    by_category: dict[uuid.UUID, list[tuple[Transaction, str]]] = {}
    for txn, category_name in transactions:
        by_category.setdefault(txn.category_id, []).append((txn, category_name))

    results: list[AnomalyRead] = []
    for rows in by_category.values():
        amounts = [float(txn.amount) for txn, _ in rows]
        flags = detector(amounts)
        for flag in flags:
            txn, category_name = rows[flag.index]
            results.append(
                AnomalyRead(
                    transaction=TransactionRead.model_validate(txn),
                    category=category_name,
                    method=method,
                    reason=flag.reason,
                )
            )
    return results
