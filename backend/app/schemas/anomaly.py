from pydantic import BaseModel

from app.schemas.transaction import TransactionRead


class AnomalyRead(BaseModel):
    transaction: TransactionRead
    category: str
    method: str
    reason: str
