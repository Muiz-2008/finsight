import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AccountType(enum.StrEnum):
    CHECKING = "checking"
    SAVINGS = "savings"
    CREDIT_CARD = "credit_card"
    CASH = "cash"
    INVESTMENT = "investment"
    OTHER = "other"


class Account(Base):
    """A container for transactions (a bank account, card, or cash wallet).

    Splitting Account out from User lets one user track several accounts
    (checking + credit card) and see transactions per-account or rolled up.
    """

    __tablename__ = "accounts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(nullable=False)
    account_type: Mapped[AccountType] = mapped_column(
        Enum(AccountType, native_enum=False, length=20), nullable=False
    )
    currency: Mapped[str] = mapped_column(default="USD")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
