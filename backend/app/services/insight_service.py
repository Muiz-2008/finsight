import uuid
from datetime import date as date_
from datetime import timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from app.analytics.cashflow import savings_rate
from app.analytics.insights import (
    budget_overage_insight,
    concentration_insight,
    savings_rate_change_insight,
    spending_change_insight,
)
from app.models.insight import Insight
from app.models.transaction import TransactionType
from app.repositories.analytics_repository import AnalyticsRepository
from app.repositories.insight_repository import InsightRepository
from app.services import analytics_service, portfolio_service
from app.services.portfolio_service import list_portfolios


def _first_of_month(d: date_) -> date_:
    return d.replace(day=1)


def _previous_month_range(d: date_) -> tuple[date_, date_]:
    this_month_start = _first_of_month(d)
    last_day_of_previous_month = this_month_start - timedelta(days=1)
    return _first_of_month(last_day_of_previous_month), last_day_of_previous_month


def _spending_insights(db: Session, user_id: uuid.UUID, today: date_) -> list[str]:
    this_month_start = _first_of_month(today)
    prev_start, prev_end = _previous_month_range(today)

    repo = AnalyticsRepository(db)
    current_totals = dict(repo.totals_by_category(user_id, this_month_start, today))
    previous_totals = dict(repo.totals_by_category(user_id, prev_start, prev_end))

    messages = []
    for category, previous in previous_totals.items():
        current = current_totals.get(category, Decimal("0"))
        message = spending_change_insight(category, previous, current)
        if message:
            messages.append(message)
    return messages


def _budget_insights(db: Session, user_id: uuid.UUID, today: date_) -> list[str]:
    this_month_start = _first_of_month(today)
    comparisons = analytics_service.get_budget_comparison(db, user_id, this_month_start, today)

    messages = []
    for comparison in comparisons:
        message = budget_overage_insight(
            comparison.category, comparison.budgeted, comparison.actual
        )
        if message:
            messages.append(message)
    return messages


def _savings_insights(db: Session, user_id: uuid.UUID, today: date_) -> list[str]:
    this_month_start = _first_of_month(today)
    prev_start, prev_end = _previous_month_range(today)
    repo = AnalyticsRepository(db)

    current_totals = repo.totals_by_type(user_id, this_month_start, today)
    previous_totals = repo.totals_by_type(user_id, prev_start, prev_end)

    current_rate = savings_rate(
        current_totals.get(TransactionType.INCOME, Decimal("0")),
        current_totals.get(TransactionType.EXPENSE, Decimal("0")),
    )
    previous_rate = savings_rate(
        previous_totals.get(TransactionType.INCOME, Decimal("0")),
        previous_totals.get(TransactionType.EXPENSE, Decimal("0")),
    )
    message = savings_rate_change_insight(previous_rate, current_rate)
    return [message] if message else []


def _portfolio_insights(db: Session, user_id: uuid.UUID) -> list[str]:
    messages = []
    for portfolio in list_portfolios(db, user_id):
        summary = portfolio_service.get_portfolio_summary(db, user_id, portfolio.id)
        if not summary.positions or summary.total_market_value <= 0:
            continue
        top = max(summary.positions, key=lambda p: p.market_value)
        weight = top.market_value / summary.total_market_value
        message = concentration_insight(top.symbol, weight)
        if message:
            messages.append(message)
    return messages


def generate_insights(db: Session, user_id: uuid.UUID) -> list[Insight]:
    """Recomputes every rule from live data and persists the results.
    Nothing here is cached or reused across calls — insights reflect the
    current state of the user's data every time they're requested.
    """
    today = date_.today()
    repo = InsightRepository(db)
    saved: list[Insight] = []

    grouped = {
        "spending": _spending_insights(db, user_id, today),
        "budget": _budget_insights(db, user_id, today),
        "savings": _savings_insights(db, user_id, today),
        "portfolio": _portfolio_insights(db, user_id),
    }
    for category, messages in grouped.items():
        if messages:
            saved.extend(repo.create_many(user_id, category, messages))
    return saved


def list_insights(db: Session, user_id: uuid.UUID) -> list[Insight]:
    return InsightRepository(db).list_for_user(user_id)
