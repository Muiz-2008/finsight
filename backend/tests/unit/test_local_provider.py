from datetime import date

from app.market_data.local_provider import LocalSyntheticProvider


def test_known_symbol_produces_a_price():
    provider = LocalSyntheticProvider()

    price = provider.get_latest_price("AAPL")

    assert price is not None
    assert price > 0


def test_unknown_symbol_returns_none_not_a_fake_price():
    # The core fix: this used to fall back to a generic default price for
    # *any* string, silently turning a typo into a fake-but-plausible
    # position instead of a clear error.
    provider = LocalSyntheticProvider()

    assert provider.get_latest_price("NOTASYMBOL") is None
    assert provider.get_history("NOTASYMBOL", date(2026, 1, 1), date(2026, 1, 31)) == []


def test_symbol_lookup_is_case_insensitive():
    provider = LocalSyntheticProvider()

    assert provider.get_latest_price("aapl") == provider.get_latest_price("AAPL")


def test_same_symbol_and_range_is_deterministic():
    provider = LocalSyntheticProvider()
    start, end = date(2026, 1, 1), date(2026, 3, 1)

    first = provider.get_history("MSFT", start, end)
    second = provider.get_history("MSFT", start, end)

    assert first == second
    assert len(first) > 0
