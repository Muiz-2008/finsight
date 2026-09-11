import uuid
from decimal import Decimal

from app.analytics.portfolio import TradeRecord, compute_holdings, value_holdings

AAPL = uuid.uuid4()


def test_single_buy_sets_avg_cost_to_purchase_price():
    trades = [TradeRecord(AAPL, "buy", Decimal("20"), Decimal("180"), Decimal("0"))]

    holdings = compute_holdings(trades)

    assert holdings[AAPL].quantity == Decimal("20")
    assert holdings[AAPL].avg_cost == Decimal("180")
    assert holdings[AAPL].cost_basis == Decimal("3600")
    assert holdings[AAPL].realized_pl == Decimal("0")


def test_market_value_and_unrealized_pl_match_spec_example():
    # Spec's worked example: 20 shares @ avg cost $180, current price $214
    # -> market value $4,280, unrealized P/L +$680.
    trades = [TradeRecord(AAPL, "buy", Decimal("20"), Decimal("180"), Decimal("0"))]
    holdings = compute_holdings(trades)

    valuations = value_holdings(holdings, {AAPL: Decimal("214")})

    assert len(valuations) == 1
    position = valuations[0]
    assert position.market_value == Decimal("4280")
    assert position.unrealized_pl == Decimal("680")


def test_two_buys_blend_into_weighted_average_cost():
    trades = [
        TradeRecord(AAPL, "buy", Decimal("10"), Decimal("100"), Decimal("0")),
        TradeRecord(AAPL, "buy", Decimal("10"), Decimal("200"), Decimal("0")),
    ]

    holdings = compute_holdings(trades)

    assert holdings[AAPL].quantity == Decimal("20")
    assert holdings[AAPL].avg_cost == Decimal("150")  # (10*100 + 10*200) / 20


def test_sell_realizes_pl_against_average_cost_and_reduces_quantity():
    trades = [
        TradeRecord(AAPL, "buy", Decimal("10"), Decimal("100"), Decimal("0")),
        TradeRecord(AAPL, "sell", Decimal("4"), Decimal("150"), Decimal("0")),
    ]

    holdings = compute_holdings(trades)

    assert holdings[AAPL].quantity == Decimal("6")
    assert holdings[AAPL].avg_cost == Decimal("100")  # unchanged by a sell
    assert holdings[AAPL].realized_pl == Decimal("200")  # 4 * (150 - 100)


def test_fully_closed_position_is_excluded_from_valuation():
    trades = [
        TradeRecord(AAPL, "buy", Decimal("10"), Decimal("100"), Decimal("0")),
        TradeRecord(AAPL, "sell", Decimal("10"), Decimal("150"), Decimal("0")),
    ]
    holdings = compute_holdings(trades)

    valuations = value_holdings(holdings, {AAPL: Decimal("150")})

    assert valuations == []
    assert holdings[AAPL].realized_pl == Decimal("500")


def test_fees_reduce_cost_basis_on_buy_and_proceeds_on_sell():
    trades = [
        TradeRecord(AAPL, "buy", Decimal("10"), Decimal("100"), Decimal("5")),
        TradeRecord(AAPL, "sell", Decimal("10"), Decimal("120"), Decimal("2")),
    ]

    holdings = compute_holdings(trades)

    # cost basis: 10*100 + 5 = 1005; proceeds: 10*120 - 2 = 1198
    assert holdings[AAPL].realized_pl == Decimal("193")


def test_missing_price_skips_position_rather_than_assuming_zero():
    trades = [TradeRecord(AAPL, "buy", Decimal("5"), Decimal("50"), Decimal("0"))]
    holdings = compute_holdings(trades)

    valuations = value_holdings(holdings, current_prices={})

    assert valuations == []
