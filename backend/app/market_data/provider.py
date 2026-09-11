"""A market-data provider is anything that can answer two questions: the
latest price for a symbol, and its daily closes over a date range. Coding
against this Protocol (not a concrete class) is what lets the app swap
providers via one config value (MARKET_DATA_PROVIDER) instead of a
code change — the spec calls for exactly this: a paid/rate-limited API
substituted by a free/local source without touching callers.
"""

from datetime import date as date_
from decimal import Decimal
from typing import Protocol


class MarketDataProvider(Protocol):
    def get_latest_price(self, symbol: str) -> Decimal | None: ...

    def get_history(self, symbol: str, start: date_, end: date_) -> list[tuple[date_, Decimal]]: ...
