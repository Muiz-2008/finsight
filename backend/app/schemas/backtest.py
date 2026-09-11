from datetime import date as date_

from pydantic import BaseModel, Field


class BacktestRequest(BaseModel):
    symbol: str = Field(min_length=1, max_length=20)
    start_date: date_
    end_date: date_
    initial_capital: float = Field(default=10_000.0, gt=0)
    short_window: int = Field(default=20, ge=2, le=200)
    long_window: int = Field(default=50, ge=3, le=400)
    transaction_cost_bps: float = Field(default=10.0, ge=0, le=1000)


class BacktestResponse(BaseModel):
    symbol: str
    start_date: date_
    end_date: date_
    strategy: str
    final_value: float
    total_return: float
    annualized_return: float | None
    annualized_volatility: float | None
    sharpe_ratio: float | None
    max_drawdown: float | None
    num_trades: int
    equity_curve: list[float]
    disclaimer: str = (
        "This is a historical simulation, not investment advice. Past "
        "performance of this rule on this data does not predict future results."
    )
