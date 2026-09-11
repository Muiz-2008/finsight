from datetime import date as date_
from decimal import Decimal

from pydantic import BaseModel

from app.analytics.cashflow import BudgetStatus
from app.schemas.transaction import TransactionRead


class CashflowSummary(BaseModel):
    date_from: date_
    date_to: date_
    income: Decimal
    expenses: Decimal
    net_cashflow: Decimal
    savings_rate: Decimal | None


class MonthlyCashflowPoint(BaseModel):
    month: date_
    income: Decimal
    expenses: Decimal
    net: Decimal


class SpendingByCategory(BaseModel):
    category: str
    total: Decimal
    percentage_of_spending: Decimal


class SpendingSummary(BaseModel):
    date_from: date_
    date_to: date_
    by_category: list[SpendingByCategory]
    largest_transactions: list[TransactionRead]


class BudgetComparison(BaseModel):
    category: str
    budgeted: Decimal
    actual: Decimal
    status: BudgetStatus
