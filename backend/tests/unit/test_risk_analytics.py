import numpy as np
import pytest

from app.analytics.risk import (
    annualized_volatility,
    beta,
    correlation_matrix,
    cumulative_returns,
    daily_returns,
    max_drawdown,
    sharpe_ratio,
)


def test_daily_returns_basic():
    returns = daily_returns([100, 110, 99])

    assert returns == pytest.approx([0.10, -0.10])


def test_daily_returns_needs_at_least_two_prices():
    assert daily_returns([100]).size == 0


def test_cumulative_returns_compounds_not_adds():
    # +10% then +10% compounds to +21%, not +20%.
    cumulative = cumulative_returns(np.array([0.10, 0.10]))

    assert cumulative[-1] == pytest.approx(0.21)


def test_annualized_volatility_of_constant_returns_is_zero():
    # Every period returns exactly 10%: no variability, so volatility is 0
    # even though the asset isn't "safe" in any everyday sense.
    returns = daily_returns([100, 110, 121, 133.1])

    assert annualized_volatility(returns) == pytest.approx(0.0, abs=1e-9)


def test_sharpe_ratio_is_none_when_volatility_is_zero():
    returns = daily_returns([100, 110, 121, 133.1])

    assert sharpe_ratio(returns) is None


def test_sharpe_ratio_is_positive_for_a_rising_volatile_series():
    returns = daily_returns([100, 105, 102, 110, 108, 115])

    result = sharpe_ratio(returns)

    assert result is not None
    assert result > 0


def test_max_drawdown_finds_the_worst_peak_to_trough_decline():
    # Peak 120 -> trough 90 is a 25% decline; the later peak of 130 has no
    # decline after it within this series.
    result = max_drawdown([100, 120, 90, 95, 130])

    assert result == pytest.approx(-0.25)


def test_max_drawdown_of_monotonically_rising_prices_is_zero():
    assert max_drawdown([100, 110, 120, 130]) == pytest.approx(0.0)


def test_beta_of_twice_as_volatile_asset_is_two():
    benchmark = np.array([0.01, 0.02, -0.01, 0.03, 0.00])
    asset = benchmark * 2

    assert beta(asset, benchmark) == pytest.approx(2.0)


def test_beta_returns_none_for_mismatched_lengths():
    assert beta(np.array([0.01, 0.02]), np.array([0.01])) is None


def test_correlation_matrix_self_correlation_is_one():
    returns = {"AAPL": np.array([0.01, 0.02, -0.01, 0.03])}
    matrix = correlation_matrix({**returns, "AAPL_COPY": returns["AAPL"]})

    assert matrix["AAPL"]["AAPL_COPY"] == pytest.approx(1.0)


def test_correlation_matrix_of_perfectly_inverse_series_is_negative_one():
    a = np.array([0.01, 0.02, -0.01, 0.03])
    matrix = correlation_matrix({"A": a, "B": -a})

    assert matrix["A"]["B"] == pytest.approx(-1.0)


def test_correlation_matrix_rejects_misaligned_lengths():
    with pytest.raises(ValueError):
        correlation_matrix({"A": np.array([0.01, 0.02]), "B": np.array([0.01])})
