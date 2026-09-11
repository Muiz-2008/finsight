import uuid
from datetime import date as date_
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Numeric, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class PriceHistory(Base):
    """Daily closing price for an asset, populated from the market data
    provider (or a local fixture in dev/test). One row per (asset, date).
    """

    __tablename__ = "price_history"
    __table_args__ = (UniqueConstraint("asset_id", "date", name="uq_price_history_asset_date"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    date: Mapped[date_] = mapped_column(Date, nullable=False)
    close_price: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
