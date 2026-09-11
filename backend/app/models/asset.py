import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AssetClass(enum.StrEnum):
    EQUITY = "equity"
    ETF = "etf"
    CRYPTO = "crypto"
    BENCHMARK = "benchmark"
    OTHER = "other"


class Asset(Base):
    """A tradable instrument. Shared reference data — not owned by any one
    user — so the same AAPL row is reused across every portfolio that holds
    it. A benchmark (e.g. SPY) is just an Asset with asset_class=BENCHMARK,
    not a separate table: it needs the exact same price history machinery.
    """

    __tablename__ = "assets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol: Mapped[str] = mapped_column(unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(nullable=False)
    asset_class: Mapped[AssetClass] = mapped_column(
        Enum(
            AssetClass,
            native_enum=False,
            length=20,
            create_constraint=True,
            name="ck_assets_asset_class",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        default=AssetClass.EQUITY,
    )
    currency: Mapped[str] = mapped_column(default="USD")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
