import uuid
from datetime import date as date_

from pydantic import BaseModel


class BenchmarkComparison(BaseModel):
    portfolio_id: uuid.UUID
    benchmark_symbol: str
    lookback_days: int
    date_from: date_ | None
    date_to: date_ | None
    portfolio_return: float | None
    benchmark_return: float | None
    outperformance: float | None  # portfolio_return - benchmark_return, percentage points
    portfolio_volatility: float | None
    benchmark_volatility: float | None
    portfolio_max_drawdown: float | None
    benchmark_max_drawdown: float | None
    beta: float | None
    warning: str | None = None
