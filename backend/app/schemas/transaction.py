import uuid
from datetime import date as date_
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.transaction import TransactionType


class TransactionCreate(BaseModel):
    account_id: uuid.UUID
    category_id: uuid.UUID | None = None
    amount: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    transaction_type: TransactionType
    description: str = Field(min_length=1, max_length=255)
    date: date_


class TransactionUpdate(BaseModel):
    account_id: uuid.UUID | None = None
    category_id: uuid.UUID | None = None
    amount: Decimal | None = Field(default=None, gt=0, max_digits=14, decimal_places=2)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    transaction_type: TransactionType | None = None
    description: str | None = Field(default=None, min_length=1, max_length=255)
    date: date_ | None = None


class TransactionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    account_id: uuid.UUID
    category_id: uuid.UUID | None
    amount: Decimal
    currency: str
    transaction_type: TransactionType
    description: str
    date: date_
    created_at: datetime


class TransactionPage(BaseModel):
    items: list[TransactionRead]
    total: int
    limit: int
    offset: int
