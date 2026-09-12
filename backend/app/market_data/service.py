import uuid
from datetime import date as date_
from datetime import timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from app.config import get_settings
from app.market_data.known_symbols import KNOWN_SYMBOLS
from app.market_data.local_provider import LocalSyntheticProvider
from app.market_data.provider import MarketDataProvider
from app.market_data.yfinance_provider import YFinanceProvider
from app.models.asset import Asset
from app.models.price_history import PriceHistory
from app.services.exceptions import ValidationError


def _build_provider() -> MarketDataProvider:
    if get_settings().market_data_provider == "yfinance":
        return YFinanceProvider()
    return LocalSyntheticProvider()


class MarketDataService:
    """Fetches prices from the configured provider and caches them into
    PriceHistory, so repeated requests for the same asset/date don't hit
    the provider (rate-limited or just slow) every time.
    """

    def __init__(self, db: Session, provider: MarketDataProvider | None = None) -> None:
        self._db = db
        self._provider = provider or _build_provider()

    def get_or_create_asset(self, symbol: str, name: str | None = None) -> Asset:
        """Looks up an existing Asset or creates one — but only for a
        symbol the active provider actually recognizes. Without this
        check, any typo silently became a real-looking position: the
        local provider used to generate a plausible price series for
        *any* string, and this method would happily create an Asset row
        for it. Now an unrecognized symbol is a clear 400, not a fake
        portfolio position.
        """
        symbol = symbol.upper()
        asset = self._db.query(Asset).filter(Asset.symbol == symbol).first()
        if asset is not None:
            return asset

        if self._provider.get_latest_price(symbol) is None:
            raise ValidationError(f"{symbol!r} is not a recognized symbol")

        known = KNOWN_SYMBOLS.get(symbol)
        asset = Asset(symbol=symbol, name=name or (known[0] if known else symbol))
        self._db.add(asset)
        self._db.commit()
        self._db.refresh(asset)
        return asset

    def get_latest_price(self, asset: Asset) -> Decimal | None:
        cached = (
            self._db.query(PriceHistory)
            .filter(PriceHistory.asset_id == asset.id)
            .order_by(PriceHistory.date.desc())
            .first()
        )
        if cached is not None and cached.date >= date_.today():
            return cached.close_price

        price = self._provider.get_latest_price(asset.symbol)
        if price is not None:
            self._cache_price(asset.id, date_.today(), price)
        elif cached is not None:
            return cached.close_price  # stale cache beats no data
        return price

    def get_history(self, asset: Asset, start: date_, end: date_) -> list[tuple[date_, Decimal]]:
        rows = (
            self._db.query(PriceHistory)
            .filter(
                PriceHistory.asset_id == asset.id,
                PriceHistory.date >= start,
                PriceHistory.date <= end,
            )
            .order_by(PriceHistory.date)
            .all()
        )
        cached_dates = {row.date for row in rows}
        expected_trading_days = {
            start + timedelta(days=i)
            for i in range((end - start).days + 1)
            if (start + timedelta(days=i)).weekday() < 5
        }
        if expected_trading_days and cached_dates >= expected_trading_days:
            return [(row.date, row.close_price) for row in rows]

        history = self._provider.get_history(asset.symbol, start, end)
        for day, price in history:
            self._cache_price(asset.id, day, price)
        return history

    def _cache_price(self, asset_id: uuid.UUID, day: date_, price: Decimal) -> None:
        existing = (
            self._db.query(PriceHistory)
            .filter(PriceHistory.asset_id == asset_id, PriceHistory.date == day)
            .first()
        )
        if existing is not None:
            existing.close_price = price
        else:
            self._db.add(PriceHistory(asset_id=asset_id, date=day, close_price=price))
        self._db.commit()
