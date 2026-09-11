"""Portfolio holdings, cost basis, and P/L — derived purely from a trade
ledger. No FastAPI, no SQLAlchemy: this module takes plain dataclasses in
and returns plain dataclasses out, so it can be unit tested in isolation
and reused from a CLI, a background job, or the API without change.
"""

import uuid
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class TradeRecord:
    asset_id: uuid.UUID
    trade_type: str  # "buy" | "sell"
    quantity: Decimal
    price: Decimal
    fees: Decimal


@dataclass
class HoldingSnapshot:
    asset_id: uuid.UUID
    quantity: Decimal
    avg_cost: Decimal  # cost basis per unit, weighted-average method
    cost_basis: Decimal  # avg_cost * quantity
    realized_pl: Decimal  # locked in from past sells, this asset only


def compute_holdings(trades: list[TradeRecord]) -> dict[uuid.UUID, HoldingSnapshot]:
    """Reduce a trade ledger to current per-asset holdings using the
    weighted-average cost method: every buy blends into a single running
    average cost per share, rather than tracking individual purchase lots
    (FIFO/LIFO). Average cost is simpler to reason about and is what most
    brokerages show by default; FIFO/LIFO matter mainly for US tax-lot
    accounting, which is out of scope here (see TRADE-OFF below).

    Trades must be processed in chronological order — average cost is
    path-dependent (a sell's realized P/L depends on the average cost *at
    that point in time*, not the final average).
    """
    holdings: dict[uuid.UUID, HoldingSnapshot] = {}

    for trade in trades:
        current = holdings.get(trade.asset_id)
        if current is None:
            current = HoldingSnapshot(
                asset_id=trade.asset_id,
                quantity=Decimal("0"),
                avg_cost=Decimal("0"),
                cost_basis=Decimal("0"),
                realized_pl=Decimal("0"),
            )

        if trade.trade_type == "buy":
            new_cost_basis = current.cost_basis + (trade.quantity * trade.price) + trade.fees
            new_quantity = current.quantity + trade.quantity
            new_avg_cost = new_cost_basis / new_quantity if new_quantity > 0 else Decimal("0")
            holdings[trade.asset_id] = HoldingSnapshot(
                asset_id=trade.asset_id,
                quantity=new_quantity,
                avg_cost=new_avg_cost,
                cost_basis=new_cost_basis,
                realized_pl=current.realized_pl,
            )

        elif trade.trade_type == "sell":
            proceeds = trade.quantity * trade.price - trade.fees
            cost_of_sold = trade.quantity * current.avg_cost
            realized_gain = proceeds - cost_of_sold
            new_quantity = current.quantity - trade.quantity
            new_cost_basis = current.avg_cost * new_quantity  # avg_cost unchanged by a sell
            holdings[trade.asset_id] = HoldingSnapshot(
                asset_id=trade.asset_id,
                quantity=new_quantity,
                avg_cost=current.avg_cost if new_quantity > 0 else Decimal("0"),
                cost_basis=new_cost_basis if new_quantity > 0 else Decimal("0"),
                realized_pl=current.realized_pl + realized_gain,
            )

    return holdings


@dataclass
class PositionValuation:
    asset_id: uuid.UUID
    quantity: Decimal
    avg_cost: Decimal
    cost_basis: Decimal
    current_price: Decimal
    market_value: Decimal
    unrealized_pl: Decimal
    realized_pl: Decimal


def value_holdings(
    holdings: dict[uuid.UUID, HoldingSnapshot],
    current_prices: dict[uuid.UUID, Decimal],
) -> list[PositionValuation]:
    """Attach live prices to derive market value and unrealized P/L.
    Positions fully closed out (quantity == 0) are skipped — their P/L is
    already captured in realized_pl and they no longer represent a holding.
    An asset with no price available is skipped with the caller expected
    to surface that as a data-quality warning, not silently treated as $0.
    """
    valuations: list[PositionValuation] = []
    for holding in holdings.values():
        if holding.quantity <= 0:
            continue
        price = current_prices.get(holding.asset_id)
        if price is None:
            continue
        market_value = holding.quantity * price
        valuations.append(
            PositionValuation(
                asset_id=holding.asset_id,
                quantity=holding.quantity,
                avg_cost=holding.avg_cost,
                cost_basis=holding.cost_basis,
                current_price=price,
                market_value=market_value,
                unrealized_pl=market_value - holding.cost_basis,
                realized_pl=holding.realized_pl,
            )
        )
    return valuations
