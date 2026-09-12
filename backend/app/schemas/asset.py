from pydantic import BaseModel


class KnownSymbol(BaseModel):
    symbol: str
    name: str
