import enum
import uuid
from datetime import date as date_
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Index, Numeric, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class TransactionType(enum.StrEnum):
    INCOME = "income"
    EXPENSE = "expense"


class Transaction(Base):
    """A single financial event. amount is always stored positive; sign is
    implied by transaction_type — this keeps CSV parsing and reporting
    unambiguous (an "amount" column with a separate "type" column, matching
    how banks/CSV exports typically represent transactions).
    """

    __tablename__ = "transactions"
    __table_args__ = (
        Index("ix_transactions_user_date", "user_id", "date"),
        # Dedup key for CSV import: the same (account, normalized-content)
        # hash can't be inserted twice.
        UniqueConstraint("account_id", "import_hash", name="uq_transaction_account_import_hash"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False
    )
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("categories.id", ondelete="SET NULL"), nullable=True
    )

    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    currency: Mapped[str] = mapped_column(default="USD")
    transaction_type: Mapped[TransactionType] = mapped_column(
        Enum(TransactionType, native_enum=False, length=10), nullable=False
    )
    description: Mapped[str] = mapped_column(nullable=False)
    date: Mapped[date_] = mapped_column(Date, nullable=False)

    # sha256 of (account_id, date, description, amount, type) — lets CSV
    # imports be re-run safely without creating duplicate rows.
    import_hash: Mapped[str] = mapped_column(nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
