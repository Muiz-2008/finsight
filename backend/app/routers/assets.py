from fastapi import APIRouter, Depends

from app.dependencies import get_current_user
from app.market_data.known_symbols import KNOWN_SYMBOLS
from app.models.user import User
from app.schemas.asset import KnownSymbol

router = APIRouter(prefix="/api/v1/assets", tags=["assets"])


@router.get("/symbols", response_model=list[KnownSymbol])
def list_known_symbols(current_user: User = Depends(get_current_user)) -> list[KnownSymbol]:
    """The symbol universe the active *local* provider validates trades
    against (see MarketDataService.get_or_create_asset) — used by the
    frontend to offer a picklist instead of free text. When
    MARKET_DATA_PROVIDER=yfinance, real tickers beyond this list are
    still accepted (that provider validates by fetching a real quote,
    not against this fixed set) — this endpoint is a curated suggestion
    list either way, not the full set of everything the API will accept.
    """
    return [
        KnownSymbol(symbol=symbol, name=name)
        for symbol, (name, _base_price) in sorted(KNOWN_SYMBOLS.items())
    ]
