import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class InsightRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    category: str
    message: str
    created_at: datetime
