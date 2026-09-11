"""Real market data via yfinance (free, no API key — scrapes Yahoo
Finance's public endpoints). Used when MARKET_DATA_PROVIDER=yfinance.
Network failures are caught and turned into None/[] rather than raised,
since a market-data outage shouldn't 500 the whole request — callers
decide how to degrade (skip the position, show stale cached data, etc).
"""

from datetime import date as date_
from decimal import Decimal


class YFinanceProvider:
    def get_latest_price(self, symbol: str) -> Decimal | None:
        try:
            import yfinance as yf

            ticker = yf.Ticker(symbol)
            history = ticker.history(period="5d")
            if history.empty:
                return None
            return Decimal(str(round(float(history["Close"].iloc[-1]), 4)))
        except Exception:
            return None

    def get_history(self, symbol: str, start: date_, end: date_) -> list[tuple[date_, Decimal]]:
        try:
            import yfinance as yf

            ticker = yf.Ticker(symbol)
            history = ticker.history(start=start.isoformat(), end=end.isoformat())
            return [
                (idx.date(), Decimal(str(round(float(close), 4))))
                for idx, close in history["Close"].items()
            ]
        except Exception:
            return []
