"""Deterministic, offline, no-API-key price generator.

Real market data (yfinance) is unreliable in exactly the places this
project needs to be reliable — CI runners and this dev sandbox routinely
have no/blocked outbound access to Yahoo Finance, and scraped data changes
daily, which would make tests non-reproducible. This provider generates a
geometric-Brownian-motion-style price series seeded deterministically by
the ticker symbol: same symbol, same date range -> same prices, every run,
everywhere. That determinism is the entire point — it's what makes
backtesting and risk-metric tests reproducible without hitting a network.
"""

import random
from datetime import date as date_
from datetime import timedelta
from decimal import ROUND_HALF_UP, Decimal

_BASE_PRICES: dict[str, float] = {
    "AAPL": 180.0,
    "MSFT": 420.0,
    "GOOGL": 170.0,
    "AMZN": 185.0,
    "SPY": 550.0,
    "QQQ": 480.0,
}
_DEFAULT_BASE_PRICE = 100.0

_ANNUAL_DRIFT = 0.08  # ~8%/yr expected return, spread over trading days
_ANNUAL_VOLATILITY = 0.22  # ~22%/yr, roughly equity-like
_TRADING_DAYS_PER_YEAR = 252


class LocalSyntheticProvider:
    def _daily_closes(self, symbol: str, start: date_, end: date_) -> list[tuple[date_, Decimal]]:
        if end < start:
            return []

        rng = random.Random(f"finsight-{symbol.upper()}")
        base_price = _BASE_PRICES.get(symbol.upper(), _DEFAULT_BASE_PRICE)
        daily_mu = _ANNUAL_DRIFT / _TRADING_DAYS_PER_YEAR
        daily_sigma = _ANNUAL_VOLATILITY / (_TRADING_DAYS_PER_YEAR**0.5)

        # Walk from a fixed epoch so a given calendar date always maps to
        # the same price regardless of what range is requested around it.
        epoch = date_(2020, 1, 1)
        price = base_price
        current = epoch
        results: list[tuple[date_, Decimal]] = []
        while current <= end:
            if current.weekday() < 5:  # trading days only
                daily_return = rng.gauss(daily_mu, daily_sigma)
                price = max(price * (1 + daily_return), 0.01)
                if current >= start:
                    results.append(
                        (current, Decimal(str(price)).quantize(Decimal("0.01"), ROUND_HALF_UP))
                    )
            current += timedelta(days=1)
        return results

    def get_latest_price(self, symbol: str) -> Decimal | None:
        today = date_.today()
        history = self._daily_closes(symbol, today - timedelta(days=14), today)
        return history[-1][1] if history else None

    def get_history(self, symbol: str, start: date_, end: date_) -> list[tuple[date_, Decimal]]:
        return self._daily_closes(symbol, start, end)
