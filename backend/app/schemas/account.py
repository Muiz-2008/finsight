import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.account import AccountType


class AccountCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    account_type: AccountType
    currency: str = Field(default="USD", min_length=3, max_length=3)


class AccountRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    account_type: AccountType
    currency: str
    created_at: datetime
