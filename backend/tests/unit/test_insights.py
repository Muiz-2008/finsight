from decimal import Decimal

from app.analytics.insights import (
    budget_overage_insight,
    concentration_insight,
    savings_rate_change_insight,
    spending_change_insight,
)


def test_spending_change_insight_reports_increase():
    message = spending_change_insight("Transport", Decimal("100"), Decimal("131"))

    assert message == "Transport spending increased 31% compared with the previous month."


def test_spending_change_insight_reports_decrease():
    message = spending_change_insight("Dining", Decimal("100"), Decimal("70"))

    assert message == "Dining spending decreased 30% compared with the previous month."


def test_spending_change_insight_silent_below_threshold():
    assert spending_change_insight("Groceries", Decimal("100"), Decimal("105")) is None


def test_spending_change_insight_silent_with_no_previous_spending():
    assert spending_change_insight("NewCategory", Decimal("0"), Decimal("50")) is None


def test_budget_overage_insight_reports_overage():
    message = budget_overage_insight("Food", Decimal("300"), Decimal("354"))

    assert message == "You have exceeded your Food budget by 18%."


def test_budget_overage_insight_silent_when_under_budget():
    assert budget_overage_insight("Food", Decimal("300"), Decimal("250")) is None


def test_budget_overage_insight_silent_for_zero_budget():
    assert budget_overage_insight("Food", Decimal("0"), Decimal("50")) is None


def test_savings_rate_change_insight_reports_increase():
    message = savings_rate_change_insight(Decimal("0.22"), Decimal("0.29"))

    assert message == "Your savings rate increased from 22% to 29%."


def test_savings_rate_change_insight_silent_below_threshold():
    assert savings_rate_change_insight(Decimal("0.22"), Decimal("0.23")) is None


def test_savings_rate_change_insight_silent_when_either_rate_undefined():
    assert savings_rate_change_insight(None, Decimal("0.29")) is None
    assert savings_rate_change_insight(Decimal("0.22"), None) is None


def test_concentration_insight_flags_heavy_concentration():
    message = concentration_insight("AAPL", Decimal("0.62"))

    assert message == "Your portfolio is heavily concentrated in AAPL (62% of market value)."


def test_concentration_insight_silent_for_diversified_portfolio():
    assert concentration_insight("AAPL", Decimal("0.25")) is None
