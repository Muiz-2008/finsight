import uuid
from datetime import date as date_

from pydantic import BaseModel


class PortfolioRisk(BaseModel):
    portfolio_id: uuid.UUID
    lookback_days: int
    date_from: date_ | None
    date_to: date_ | None
    annualized_volatility: float | None
    sharpe_ratio: float | None
    max_drawdown: float | None
    cumulative_return: float | None
    correlation_matrix: dict[str, dict[str, float]]
    warning: str | None = None
