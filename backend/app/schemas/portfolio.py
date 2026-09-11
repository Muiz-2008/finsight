import uuid
from datetime import date as date_
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.trade import TradeType


class PortfolioCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class PortfolioRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    created_at: datetime


class TradeCreate(BaseModel):
    symbol: str = Field(min_length=1, max_length=20)
    trade_type: TradeType
    quantity: Decimal = Field(gt=0, max_digits=18, decimal_places=6)
    price: Decimal = Field(gt=0, max_digits=14, decimal_places=4)
    fees: Decimal = Field(default=Decimal("0"), ge=0, max_digits=10, decimal_places=2)
    trade_date: date_


class TradeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    trade_type: TradeType
    quantity: Decimal
    price: Decimal
    fees: Decimal
    trade_date: date_


class PositionRead(BaseModel):
    symbol: str
    quantity: Decimal
    avg_cost: Decimal
    cost_basis: Decimal
    current_price: Decimal
    market_value: Decimal
    unrealized_pl: Decimal
    realized_pl: Decimal


class PortfolioSummary(BaseModel):
    portfolio_id: uuid.UUID
    positions: list[PositionRead]
    total_market_value: Decimal
    total_cost_basis: Decimal
    total_unrealized_pl: Decimal
    total_realized_pl: Decimal
