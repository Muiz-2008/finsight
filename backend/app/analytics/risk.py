"""Portfolio risk metrics: returns, volatility, Sharpe ratio, max drawdown,
beta, and correlation. Pure NumPy on plain float sequences — no ORM, no
HTTP.

Why float here and Decimal in app/analytics/portfolio.py: cost basis and
market value are *ledger* amounts — numbers a user is owed or owes, where
a one-cent rounding error is a real, user-visible bug. Volatility and
Sharpe ratio are *statistical estimates* derived from noisy historical
data; the estimation error from a finite sample of returns (easily several
percentage points) dwarfs float64's ~1e-15 relative error by many orders
of magnitude. Using Decimal here would buy false precision at a real
performance cost, for calculations that are approximations by nature.

None of these metrics are predictions. They describe what already
happened; nothing here forecasts what happens next.
"""

import numpy as np


def daily_returns(prices: list[float]) -> np.ndarray:
    """Simple (not log) returns: (p[t] - p[t-1]) / p[t-1]."""
    if len(prices) < 2:
        return np.array([])
    p = np.asarray(prices, dtype=float)
    return (p[1:] - p[:-1]) / p[:-1]


def cumulative_returns(returns: np.ndarray) -> np.ndarray:
    """Running total return if each period's return compounds on the last.
    cumulative_returns([0.10, 0.10])[-1] == 0.21 (10% then 10% = 21% total,
    not 20% — compounding, not addition).
    """
    return np.cumprod(1 + returns) - 1


def annualized_volatility(returns: np.ndarray, periods_per_year: int = 252) -> float | None:
    """Std dev of returns, scaled to a yearly figure by sqrt(time) — the
    standard assumption that returns in different periods are independent
    and identically distributed, so variance (not std) scales linearly
    with time and std scales with its square root. 252 is the typical
    count of US trading days in a year.
    """
    if len(returns) < 2:
        return None
    return float(np.std(returns, ddof=1) * np.sqrt(periods_per_year))


def sharpe_ratio(
    returns: np.ndarray, risk_free_rate: float = 0.0, periods_per_year: int = 252
) -> float | None:
    """Risk-adjusted return: excess return per unit of volatility.

    A Sharpe of 1.0 isn't "good" in the abstract — it means the strategy
    earned 1 unit of return for every unit of volatility risked. Compare
    Sharpe ratios to each other (this portfolio vs. that one, or vs. a
    benchmark), not to a fixed threshold. risk_free_rate is annualized;
    it's converted to a per-period rate before subtracting.
    """
    if len(returns) < 2:
        return None
    period_rf = risk_free_rate / periods_per_year
    excess = returns - period_rf
    std = np.std(excess, ddof=1)
    # A tolerance, not `== 0`: floating-point returns computed from prices
    # (e.g. a constant 10%/period series) rarely hit exactly zero std due
    # to rounding, which would otherwise blow up into a meaningless ratio
    # in the 1e16 range instead of the "undefined" it actually is.
    if np.isclose(std, 0, atol=1e-12):
        return None
    return float(np.mean(excess) / std * np.sqrt(periods_per_year))


def max_drawdown(prices: list[float]) -> float | None:
    """The worst peak-to-trough decline over the series, as a negative
    fraction (-0.25 == a 25% drop from the prior high). Uses the running
    maximum seen *so far* at each point — a drawdown can only be measured
    against a peak that has already occurred, not a future one
    (the same look-ahead-bias discipline the backtester enforces).
    """
    if len(prices) < 2:
        return None
    p = np.asarray(prices, dtype=float)
    running_peak = np.maximum.accumulate(p)
    drawdowns = (p - running_peak) / running_peak
    return float(np.min(drawdowns))


def beta(asset_returns: np.ndarray, benchmark_returns: np.ndarray) -> float | None:
    """Sensitivity of the asset to the benchmark: cov(asset, benchmark) /
    var(benchmark). beta=1.5 means the asset historically moved 1.5x the
    benchmark's moves. Requires equal-length, date-aligned return series —
    a caller that hands in mismatched dates gets a mathematically
    meaningless number back, so callers are responsible for alignment
    (see app.analytics.benchmark).
    """
    if len(asset_returns) != len(benchmark_returns) or len(asset_returns) < 2:
        return None
    benchmark_var = np.var(benchmark_returns, ddof=1)
    if benchmark_var == 0:
        return None
    covariance = np.cov(asset_returns, benchmark_returns, ddof=1)[0, 1]
    return float(covariance / benchmark_var)


def correlation_matrix(returns_by_symbol: dict[str, np.ndarray]) -> dict[str, dict[str, float]]:
    """Pearson correlation between every pair of assets' returns —
    diversification only reduces risk to the extent holdings move
    independently; a portfolio of highly-correlated assets is less
    diversified than the number of tickers suggests.
    """
    symbols = list(returns_by_symbol.keys())
    if len(symbols) < 2:
        return {}
    lengths = {len(returns_by_symbol[s]) for s in symbols}
    if len(lengths) != 1:
        raise ValueError("all return series must be the same length (aligned dates)")

    matrix = np.corrcoef([returns_by_symbol[s] for s in symbols])
    return {
        row_symbol: {
            col_symbol: float(matrix[i, j]) for j, col_symbol in enumerate(symbols)
        }
        for i, row_symbol in enumerate(symbols)
    }
