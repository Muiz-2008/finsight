"""Cash flow, spending, and budget math. Pure Decimal arithmetic on plain
inputs — no ORM, no HTTP — so every edge case (zero income, zero spend,
an over-budget category) is a one-line unit test, not something that
needs a database fixture to exercise.
"""

import enum
from decimal import Decimal


def savings_rate(income: Decimal, expenses: Decimal) -> Decimal | None:
    """(income - expenses) / income, as a fraction (0.25 == 25%).

    Returns None for zero income rather than raising or returning 0 —
    "0% savings rate" and "undefined, no income to save from" are different
    facts, and collapsing them would mislead a dashboard into showing a
    number that means something else entirely.
    """
    if income == 0:
        return None
    return (income - expenses) / income


def percentage_change(previous: Decimal, current: Decimal) -> Decimal | None:
    """(current - previous) / previous, as a fraction.

    Returns None when `previous` is 0 — "infinite percent increase from
    zero" is not a meaningful number to plot or alert on.
    """
    if previous == 0:
        return None
    return (current - previous) / previous


class BudgetStatus(enum.StrEnum):
    UNDER = "under"
    APPROACHING = "approaching"  # >= 80% of limit
    OVER = "over"


def classify_budget(actual: Decimal, limit: Decimal) -> BudgetStatus:
    if limit <= 0:
        return BudgetStatus.OVER if actual > 0 else BudgetStatus.UNDER
    ratio = actual / limit
    if ratio >= 1:
        return BudgetStatus.OVER
    if ratio >= Decimal("0.8"):
        return BudgetStatus.APPROACHING
    return BudgetStatus.UNDER
