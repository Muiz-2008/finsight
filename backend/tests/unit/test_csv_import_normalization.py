from app.ingestion.csv_importer import _normalize_type
from app.models.transaction import TransactionType


def test_normalizes_common_income_spellings():
    for raw in ["income", "Income", " INCOME ", "in", "credit"]:
        assert _normalize_type(raw) == TransactionType.INCOME


def test_normalizes_common_expense_spellings():
    for raw in ["expense", "Expense", "out", "debit"]:
        assert _normalize_type(raw) == TransactionType.EXPENSE


def test_rejects_unrecognized_type():
    assert _normalize_type("transfer") is None
    assert _normalize_type("") is None
