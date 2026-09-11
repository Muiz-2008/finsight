import uuid
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class BudgetCreate(BaseModel):
    category_id: uuid.UUID
    monthly_limit: Decimal = Field(gt=0, max_digits=14, decimal_places=2)


class BudgetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    category_id: uuid.UUID
    monthly_limit: Decimal
