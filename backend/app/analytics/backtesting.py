"""A minimal, honest backtesting engine: one strategy (moving-average
crossover), implemented carefully rather than three strategies implemented
sloppily. The single most important property of any backtester is that it
cannot see the future — this module is built around enforcing that,
mechanically, not just promising it in a docstring.

THIS IS A SIMULATION, NOT INVESTMENT ADVICE. Past price data run through
a rule is not a forecast of what that rule will do next; markets that
produced these historical prices are not obligated to keep behaving the
same way.
"""

from dataclasses import dataclass, field

import numpy as np

from app.analytics.risk import annualized_volatility, daily_returns, max_drawdown, sharpe_ratio


def moving_average_crossover_signals(
    prices: list[float], short_window: int, long_window: int
) -> list[int]:
    """Long-only signal: 1 (fully invested) once the short moving average
    is above the long moving average, else 0 (cash) — no shorting, which
    keeps the model simple and avoids margin/borrow-cost assumptions this
    project doesn't attempt to model.

    signal[t] is computed using only prices[0 : t+1] — the close of day t
    and everything before it. It never looks at prices[t+1:]. Before
    `long_window` days of history exist, the signal is 0 (insufficient
    data to decide, so stay in cash rather than guess).
    """
    if short_window >= long_window:
        raise ValueError("short_window must be less than long_window")

    signals = [0] * len(prices)
    for t in range(len(prices)):
        if t + 1 < long_window:
            continue
        short_ma = sum(prices[t - short_window + 1 : t + 1]) / short_window
        long_ma = sum(prices[t - long_window + 1 : t + 1]) / long_window
        signals[t] = 1 if short_ma > long_ma else 0
    return signals


@dataclass(frozen=True)
class BacktestResult:
    final_value: float
    total_return: float
    annualized_return: float | None
    annualized_volatility: float | None
    sharpe_ratio: float | None
    max_drawdown: float | None
    num_trades: int
    equity_curve: list[float] = field(default_factory=list)


def run_backtest(
    prices: list[float],
    signals: list[int],
    initial_capital: float = 10_000.0,
    transaction_cost_bps: float = 10.0,
    periods_per_year: int = 252,
    risk_free_rate: float = 0.0,
) -> BacktestResult:
    """Applies `signals` to `prices` with a strict one-period lag: the
    position decided using data through day t (signals[t]) is applied to
    the return realized from day t to day t+1 (asset_returns[t]) — never
    to day t's own return, and never using information from day t+1 or
    later. This lag is THE mechanism that prevents look-ahead bias here;
    everything else in this function is bookkeeping around it.

    transaction_cost_bps models a proportional cost (basis points of
    portfolio value) charged whenever the position changes — a strategy
    that flips in and out constantly pays for it, the same as in reality.
    """
    if len(prices) != len(signals):
        raise ValueError("prices and signals must be the same length")
    if len(prices) < 2:
        return BacktestResult(initial_capital, 0.0, None, None, None, None, 0, [initial_capital])

    asset_returns = daily_returns(prices)  # asset_returns[t] = return from day t to day t+1

    equity = [initial_capital]
    num_trades = 0
    position_held = 0

    for t in range(len(asset_returns)):
        desired_position = signals[t]
        if desired_position != position_held:
            num_trades += 1
            cost_fraction = transaction_cost_bps / 10_000 * abs(desired_position - position_held)
            equity[-1] *= 1 - cost_fraction
        position_held = desired_position

        period_return = position_held * asset_returns[t]
        equity.append(equity[-1] * (1 + period_return))

    strategy_returns = daily_returns(equity)
    total_return = equity[-1] / initial_capital - 1
    years = len(asset_returns) / periods_per_year
    annualized_return = (1 + total_return) ** (1 / years) - 1 if years > 0 else None

    return BacktestResult(
        final_value=equity[-1],
        total_return=total_return,
        annualized_return=annualized_return,
        annualized_volatility=annualized_volatility(np.asarray(strategy_returns), periods_per_year),
        sharpe_ratio=sharpe_ratio(np.asarray(strategy_returns), risk_free_rate, periods_per_year),
        max_drawdown=max_drawdown(equity),
        num_trades=num_trades,
        equity_curve=equity,
    )
