from decimal import Decimal

from app.analytics.cashflow import BudgetStatus, classify_budget, percentage_change, savings_rate


def test_savings_rate_basic():
    assert savings_rate(Decimal("1000"), Decimal("750")) == Decimal("0.25")


def test_savings_rate_handles_zero_income():
    assert savings_rate(Decimal("0"), Decimal("100")) is None


def test_savings_rate_can_be_negative_when_overspending():
    assert savings_rate(Decimal("1000"), Decimal("1200")) == Decimal("-0.2")


def test_percentage_change_basic():
    assert percentage_change(Decimal("100"), Decimal("131")) == Decimal("0.31")


def test_percentage_change_handles_zero_previous():
    assert percentage_change(Decimal("0"), Decimal("50")) is None


def test_classify_budget_under():
    assert classify_budget(Decimal("50"), Decimal("300")) == BudgetStatus.UNDER


def test_classify_budget_approaching_at_80_percent():
    assert classify_budget(Decimal("240"), Decimal("300")) == BudgetStatus.APPROACHING


def test_classify_budget_over():
    assert classify_budget(Decimal("354"), Decimal("300")) == BudgetStatus.OVER


def test_classify_budget_zero_limit_with_no_spend_is_under():
    assert classify_budget(Decimal("0"), Decimal("0")) == BudgetStatus.UNDER


def test_classify_budget_zero_limit_with_any_spend_is_over():
    assert classify_budget(Decimal("1"), Decimal("0")) == BudgetStatus.OVER
