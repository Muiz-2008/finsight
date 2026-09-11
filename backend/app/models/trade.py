import enum
import uuid
from datetime import date as date_
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Numeric, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class TradeType(enum.StrEnum):
    BUY = "buy"
    SELL = "sell"


class Trade(Base):
    """A single buy/sell event. This is the source of truth for holdings —
    current quantity, cost basis, and realized/unrealized P/L are all
    *derived* from the trade ledger (see app/analytics/portfolio.py),
    never stored as a separately-updated "current holding" row that could
    drift out of sync with what was actually bought and sold.
    """

    __tablename__ = "trades"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    portfolio_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("portfolios.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assets.id", ondelete="RESTRICT"), nullable=False
    )

    trade_type: Mapped[TradeType] = mapped_column(
        Enum(TradeType, native_enum=False, length=10), nullable=False
    )
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    fees: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0"))
    trade_date: Mapped[date_] = mapped_column(Date, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
