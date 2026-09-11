import uuid
from datetime import date as date_
from decimal import Decimal

from sqlalchemy.orm import Session

from app.analytics.cashflow import classify_budget, savings_rate
from app.models.transaction import TransactionType
from app.repositories.analytics_repository import AnalyticsRepository
from app.repositories.budget_repository import BudgetRepository
from app.repositories.category_repository import CategoryRepository
from app.schemas.analytics import (
    BudgetComparison,
    CashflowSummary,
    MonthlyCashflowPoint,
    SpendingByCategory,
    SpendingSummary,
)
from app.schemas.transaction import TransactionRead


def get_cashflow_summary(
    db: Session, user_id: uuid.UUID, date_from: date_, date_to: date_
) -> CashflowSummary:
    totals = AnalyticsRepository(db).totals_by_type(user_id, date_from, date_to)
    income = totals.get(TransactionType.INCOME, Decimal("0"))
    expenses = totals.get(TransactionType.EXPENSE, Decimal("0"))
    return CashflowSummary(
        date_from=date_from,
        date_to=date_to,
        income=income,
        expenses=expenses,
        net_cashflow=income - expenses,
        savings_rate=savings_rate(income, expenses),
    )


def get_monthly_cashflow(
    db: Session, user_id: uuid.UUID, date_from: date_, date_to: date_
) -> list[MonthlyCashflowPoint]:
    rows = AnalyticsRepository(db).monthly_totals(user_id, date_from, date_to)

    by_month: dict[date_, dict[TransactionType, Decimal]] = {}
    for month, ttype, total in rows:
        by_month.setdefault(month, {})[ttype] = total

    points = []
    for month in sorted(by_month):
        income = by_month[month].get(TransactionType.INCOME, Decimal("0"))
        expenses = by_month[month].get(TransactionType.EXPENSE, Decimal("0"))
        points.append(
            MonthlyCashflowPoint(
                month=month, income=income, expenses=expenses, net=income - expenses
            )
        )
    return points


def get_spending_summary(
    db: Session, user_id: uuid.UUID, date_from: date_, date_to: date_, top_n: int = 5
) -> SpendingSummary:
    repo = AnalyticsRepository(db)
    category_totals = repo.totals_by_category(user_id, date_from, date_to)
    total_spending = sum((t for _, t in category_totals), Decimal("0"))

    by_category = [
        SpendingByCategory(
            category=name,
            total=total,
            percentage_of_spending=(
                (total / total_spending * 100) if total_spending > 0 else Decimal("0")
            ),
        )
        for name, total in category_totals
    ]

    top_transactions = repo.top_transactions(user_id, date_from, date_to, top_n)

    return SpendingSummary(
        date_from=date_from,
        date_to=date_to,
        by_category=by_category,
        largest_transactions=[TransactionRead.model_validate(t) for t in top_transactions],
    )


def get_budget_comparison(
    db: Session, user_id: uuid.UUID, date_from: date_, date_to: date_
) -> list[BudgetComparison]:
    budgets = BudgetRepository(db).list_for_user(user_id)
    if not budgets:
        return []

    category_totals = dict(AnalyticsRepository(db).totals_by_category(user_id, date_from, date_to))
    categories = {c.id: c.name for c in CategoryRepository(db).list_for_user(user_id)}

    comparisons = []
    for budget in budgets:
        category_name = categories.get(budget.category_id, "Unknown")
        actual = category_totals.get(category_name, Decimal("0"))
        comparisons.append(
            BudgetComparison(
                category=category_name,
                budgeted=budget.monthly_limit,
                actual=actual,
                status=classify_budget(actual, budget.monthly_limit),
            )
        )
    return comparisons
