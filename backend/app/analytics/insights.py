"""Rule-based insight generation: every function here takes numbers
already computed elsewhere (category totals, savings rates, portfolio
weights) and turns a real, checkable fact into a plain-English sentence.

Nothing here calls an LLM or invents a number. If a rule's inputs don't
clear its threshold, it returns None — silence, not a fabricated insight.
This is deliberately "boring" and that's the point: every sentence this
module produces is traceable back to an arithmetic comparison a user
could redo by hand.
"""

from decimal import Decimal

from app.analytics.cashflow import percentage_change


def spending_change_insight(
    category: str, previous: Decimal, current: Decimal, threshold_pct: Decimal = Decimal("15")
) -> str | None:
    change = percentage_change(previous, current)
    if change is None or abs(change * 100) < threshold_pct:
        return None
    direction = "increased" if change > 0 else "decreased"
    return (
        f"{category} spending {direction} {abs(change * 100):.0f}% "
        f"compared with the previous month."
    )


def budget_overage_insight(category: str, budgeted: Decimal, actual: Decimal) -> str | None:
    if budgeted <= 0 or actual <= budgeted:
        return None
    overage_pct = (actual - budgeted) / budgeted * 100
    return f"You have exceeded your {category} budget by {overage_pct:.0f}%."


def savings_rate_change_insight(
    previous_rate: Decimal | None,
    current_rate: Decimal | None,
    threshold_pct: Decimal = Decimal("3"),
) -> str | None:
    if previous_rate is None or current_rate is None:
        return None
    change_pct = (current_rate - previous_rate) * 100
    if abs(change_pct) < threshold_pct:
        return None
    direction = "increased" if change_pct > 0 else "decreased"
    return (
        f"Your savings rate {direction} from {previous_rate * 100:.0f}% "
        f"to {current_rate * 100:.0f}%."
    )


def concentration_insight(
    top_symbol: str, top_weight: Decimal, threshold: Decimal = Decimal("0.5")
) -> str | None:
    if top_weight < threshold:
        return None
    return (
        f"Your portfolio is heavily concentrated in {top_symbol} "
        f"({top_weight * 100:.0f}% of market value)."
    )
