"""The set of symbols FinSight recognizes when the local synthetic
provider is active (MARKET_DATA_PROVIDER=local, the default).

This exists to close a real gap: without it, any string typed into a
"symbol" field would silently succeed — the local provider generated a
plausible-looking price series for literally anything, since it fell back
to a generic default price for unrecognized symbols instead of rejecting
them. A user mistyping "AAPL" as "APPL" got a fake position with fake
data instead of a clear error. Recording a trade now validates the
symbol against this set first (see MarketDataService.get_or_create_asset)
and rejects anything not on it, and GET /api/v1/assets/symbols exposes
the same list so the frontend can offer it as a picklist instead of free
text — one source of truth for both the validation and the UI.

When MARKET_DATA_PROVIDER=yfinance, this list isn't used for validation —
YFinanceProvider validates by actually attempting to fetch a real quote,
which correctly accepts any real ticker rather than being limited to this
curated set.
"""

KNOWN_SYMBOLS: dict[str, tuple[str, float]] = {
    "AAPL": ("Apple Inc.", 180.0),
    "MSFT": ("Microsoft Corporation", 420.0),
    "GOOGL": ("Alphabet Inc. (Class A)", 170.0),
    "AMZN": ("Amazon.com, Inc.", 185.0),
    "META": ("Meta Platforms, Inc.", 590.0),
    "NVDA": ("NVIDIA Corporation", 135.0),
    "TSLA": ("Tesla, Inc.", 250.0),
    "NFLX": ("Netflix, Inc.", 700.0),
    "JPM": ("JPMorgan Chase & Co.", 210.0),
    "V": ("Visa Inc.", 280.0),
    "MA": ("Mastercard Incorporated", 470.0),
    "DIS": ("The Walt Disney Company", 110.0),
    "KO": ("The Coca-Cola Company", 62.0),
    "WMT": ("Walmart Inc.", 68.0),
    "JNJ": ("Johnson & Johnson", 155.0),
    "SPY": ("SPDR S&P 500 ETF Trust", 550.0),
    "QQQ": ("Invesco QQQ Trust (Nasdaq-100)", 480.0),
    "VOO": ("Vanguard S&P 500 ETF", 505.0),
    "DIA": ("SPDR Dow Jones Industrial Average ETF", 400.0),
    "IWM": ("iShares Russell 2000 ETF", 210.0),
}
