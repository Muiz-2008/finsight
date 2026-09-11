"""CSV -> Transaction pipeline: validate -> normalize -> dedup -> insert.

Pandas earns its place at the *parsing and validation* stage: reading a
CSV into a DataFrame gives vectorized type coercion (`pd.to_datetime`,
`pd.to_numeric`) and vectorized null/invalid-row detection across
potentially hundreds of thousands of rows, which would be far slower as a
plain Python per-row loop.

Pandas deliberately stops being used once rows are valid. The actual
insert is a single bulk SQL statement (see
TransactionRepository.bulk_insert_ignore_duplicates) built from plain
Transaction ORM objects — looping in Python to call `session.add()` per
row, or worse, going through DataFrame.apply() to hit the database, would
turn one INSERT into N round trips for no benefit; Pandas has no role to
play in "write this to Postgres".
"""

import io
import uuid
from dataclasses import dataclass, field
from datetime import date as date_
from decimal import Decimal, InvalidOperation

import pandas as pd
from sqlalchemy.orm import Session

from app.ingestion.dedup import compute_import_hash
from app.models.category import Category
from app.models.transaction import Transaction, TransactionType
from app.repositories.transaction_repository import TransactionRepository

REQUIRED_COLUMNS = {"date", "description", "amount", "category", "type"}


@dataclass
class ImportReport:
    total_rows: int = 0
    imported: int = 0
    duplicates: int = 0
    invalid: int = 0
    errors: list[str] = field(default_factory=list)


def _normalize_type(raw: str) -> TransactionType | None:
    value = str(raw).strip().lower()
    if value in ("income", "in", "credit"):
        return TransactionType.INCOME
    if value in ("expense", "out", "debit"):
        return TransactionType.EXPENSE
    return None


def import_transactions_csv(
    db: Session,
    user_id: uuid.UUID,
    account_id: uuid.UUID,
    file_bytes: bytes,
) -> ImportReport:
    report = ImportReport()

    try:
        df = pd.read_csv(io.BytesIO(file_bytes), dtype=str, keep_default_na=False)
    except Exception as exc:
        report.errors.append(f"Could not parse file as CSV: {exc}")
        return report

    missing = REQUIRED_COLUMNS - set(c.strip().lower() for c in df.columns)
    if missing:
        report.errors.append(f"Missing required column(s): {', '.join(sorted(missing))}")
        return report
    df.columns = [c.strip().lower() for c in df.columns]

    # Drop fully-empty rows (common in hand-edited CSVs) before counting —
    # they aren't "invalid data", they're not data at all.
    df = df[~(df.apply(lambda row: all(str(v).strip() == "" for v in row), axis=1))]
    report.total_rows = len(df)

    # Fetch the user's categories once (name -> id, case-insensitive) rather
    # than querying per row.
    categories = db.query(Category).filter(Category.user_id == user_id).all()
    category_by_name = {c.name.strip().lower(): c.id for c in categories}

    valid_transactions: list[Transaction] = []

    for row_number, row in enumerate(df.itertuples(index=False), start=2):  # +1 header, +1 1-index
        row_dict = row._asdict()
        errors_for_row: list[str] = []

        parsed_date: date_ | None = None
        try:
            parsed_date = pd.to_datetime(row_dict["date"], errors="raise").date()
        except (ValueError, TypeError):
            errors_for_row.append("invalid date")

        amount: Decimal | None = None
        try:
            amount = Decimal(str(row_dict["amount"]).replace(",", "").strip())
            if amount <= 0:
                errors_for_row.append("amount must be positive")
                amount = None
        except (InvalidOperation, ValueError):
            errors_for_row.append("invalid amount")

        transaction_type = _normalize_type(row_dict["type"])
        if transaction_type is None:
            errors_for_row.append("invalid type (expected income/expense)")

        description = str(row_dict["description"]).strip()
        if not description:
            errors_for_row.append("missing description")

        category_name = str(row_dict["category"]).strip()
        category_id = category_by_name.get(category_name.lower()) if category_name else None

        if errors_for_row:
            report.invalid += 1
            report.errors.append(f"row {row_number}: {', '.join(errors_for_row)}")
            continue

        valid_transactions.append(
            Transaction(
                id=uuid.uuid4(),
                user_id=user_id,
                account_id=account_id,
                category_id=category_id,
                amount=amount,
                transaction_type=transaction_type,
                description=description,
                date=parsed_date,
                import_hash=compute_import_hash(
                    account_id, parsed_date, description, amount, transaction_type
                ),
            )
        )

    inserted = TransactionRepository(db).bulk_insert_ignore_duplicates(valid_transactions)
    report.imported = inserted
    report.duplicates = len(valid_transactions) - inserted
    return report
