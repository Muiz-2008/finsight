import uuid
from datetime import date as date_
from datetime import timedelta

import numpy as np
from sqlalchemy.orm import Session

from app.analytics.risk import (
    annualized_volatility,
    cumulative_returns,
    daily_returns,
    max_drawdown,
)
from app.analytics.risk import beta as compute_beta
from app.market_data.service import MarketDataService
from app.schemas.benchmark import BenchmarkComparison
from app.services.portfolio_service import get_owned_portfolio, portfolio_value_series


def get_benchmark_comparison(
    db: Session,
    user_id: uuid.UUID,
    portfolio_id: uuid.UUID,
    benchmark_symbol: str = "SPY",
    lookback_days: int = 252,
) -> BenchmarkComparison:
    """Compare a portfolio's trailing performance against a benchmark
    (default: SPY, a common S&P 500 proxy). Aligns the two series to their
    *overlapping* dates only — a portfolio with a shorter price history
    than the benchmark (e.g. a recently-added holding) is compared over
    the shorter, honestly-available window rather than padded with
    assumed data.
    """
    get_owned_portfolio(db, user_id, portfolio_id)
    series = portfolio_value_series(db, portfolio_id, lookback_days)

    empty = BenchmarkComparison(
        portfolio_id=portfolio_id,
        benchmark_symbol=benchmark_symbol.upper(),
        lookback_days=lookback_days,
        date_from=None,
        date_to=None,
        portfolio_return=None,
        benchmark_return=None,
        outperformance=None,
        portfolio_volatility=None,
        benchmark_volatility=None,
        portfolio_max_drawdown=None,
        benchmark_max_drawdown=None,
        beta=None,
        warning="No open positions to compare.",
    )
    if series is None or not series.dates:
        return empty

    market_data = MarketDataService(db)
    benchmark_asset = market_data.get_or_create_asset(benchmark_symbol)
    end = date_.today()
    start = end - timedelta(days=lookback_days)
    benchmark_history = dict(market_data.get_history(benchmark_asset, start, end))

    common_dates = sorted(set(series.dates) & set(benchmark_history.keys()))
    if len(common_dates) < 2:
        empty.warning = "Not enough overlapping price history with the benchmark."
        return empty

    portfolio_by_date = dict(zip(series.dates, series.values, strict=True))
    portfolio_values = [portfolio_by_date[d] for d in common_dates]
    benchmark_values = [float(benchmark_history[d]) for d in common_dates]

    portfolio_returns = daily_returns(portfolio_values)
    benchmark_returns = daily_returns(benchmark_values)

    portfolio_cum = (
        cumulative_returns(portfolio_returns) if portfolio_returns.size else np.array([])
    )
    benchmark_cum = (
        cumulative_returns(benchmark_returns) if benchmark_returns.size else np.array([])
    )

    portfolio_return = float(portfolio_cum[-1]) if portfolio_cum.size else None
    benchmark_return = float(benchmark_cum[-1]) if benchmark_cum.size else None
    outperformance = (
        (portfolio_return - benchmark_return)
        if portfolio_return is not None and benchmark_return is not None
        else None
    )

    warning = series.warning
    if len(common_dates) < 20:
        warning = (
            f"Only {len(common_dates)} overlapping trading days with the benchmark; "
            "comparison over such a short window is unreliable."
        )

    return BenchmarkComparison(
        portfolio_id=portfolio_id,
        benchmark_symbol=benchmark_symbol.upper(),
        lookback_days=lookback_days,
        date_from=common_dates[0],
        date_to=common_dates[-1],
        portfolio_return=portfolio_return,
        benchmark_return=benchmark_return,
        outperformance=outperformance,
        portfolio_volatility=annualized_volatility(portfolio_returns),
        benchmark_volatility=annualized_volatility(benchmark_returns),
        portfolio_max_drawdown=max_drawdown(portfolio_values),
        benchmark_max_drawdown=max_drawdown(benchmark_values),
        beta=compute_beta(portfolio_returns, benchmark_returns),
        warning=warning,
    )
