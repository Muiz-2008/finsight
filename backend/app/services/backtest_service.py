from sqlalchemy.orm import Session

from app.analytics.backtesting import moving_average_crossover_signals, run_backtest
from app.market_data.service import MarketDataService
from app.schemas.backtest import BacktestRequest, BacktestResponse
from app.services.exceptions import ValidationError


def run_moving_average_backtest(db: Session, request: BacktestRequest) -> BacktestResponse:
    market_data = MarketDataService(db)
    asset = market_data.get_or_create_asset(request.symbol)
    history = market_data.get_history(asset, request.start_date, request.end_date)

    if len(history) < request.long_window + 2:
        raise ValidationError(
            f"Not enough price history for {request.symbol} in this date range "
            f"({len(history)} days available, need at least {request.long_window + 2})."
        )

    prices = [float(price) for _, price in history]
    signals = moving_average_crossover_signals(prices, request.short_window, request.long_window)
    result = run_backtest(
        prices,
        signals,
        initial_capital=request.initial_capital,
        transaction_cost_bps=request.transaction_cost_bps,
    )

    return BacktestResponse(
        symbol=request.symbol.upper(),
        start_date=request.start_date,
        end_date=request.end_date,
        strategy=f"moving_average_crossover({request.short_window},{request.long_window})",
        final_value=result.final_value,
        total_return=result.total_return,
        annualized_return=result.annualized_return,
        annualized_volatility=result.annualized_volatility,
        sharpe_ratio=result.sharpe_ratio,
        max_drawdown=result.max_drawdown,
        num_trades=result.num_trades,
        equity_curve=result.equity_curve,
    )
