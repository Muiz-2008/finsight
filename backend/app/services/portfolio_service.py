import uuid
from datetime import date as date_
from datetime import timedelta
from decimal import Decimal

import numpy as np
from sqlalchemy.orm import Session

from app.analytics.portfolio import HoldingSnapshot, TradeRecord, compute_holdings, value_holdings
from app.analytics.risk import (
    annualized_volatility,
    correlation_matrix,
    cumulative_returns,
    daily_returns,
    max_drawdown,
    sharpe_ratio,
)
from app.market_data.service import MarketDataService
from app.models.asset import Asset
from app.models.portfolio import Portfolio
from app.models.trade import Trade
from app.repositories.portfolio_repository import PortfolioRepository
from app.schemas.portfolio import PortfolioSummary, PositionRead, TradeCreate
from app.schemas.risk import PortfolioRisk
from app.services.exceptions import NotFoundError


def _holdings_and_assets(
    db: Session, portfolio_id: uuid.UUID
) -> tuple[dict[uuid.UUID, HoldingSnapshot], dict[uuid.UUID, Asset]]:
    trades = PortfolioRepository(db).list_trades(portfolio_id)
    records = [
        TradeRecord(
            asset_id=t.asset_id,
            trade_type=t.trade_type.value,
            quantity=t.quantity,
            price=t.price,
            fees=t.fees,
        )
        for t in trades
    ]
    holdings = compute_holdings(records)
    asset_ids = list(holdings.keys())
    assets_by_id = {a.id: a for a in db.query(Asset).filter(Asset.id.in_(asset_ids)).all()}
    return holdings, assets_by_id


def list_portfolios(db: Session, user_id: uuid.UUID) -> list[Portfolio]:
    return PortfolioRepository(db).list_for_user(user_id)


def create_portfolio(db: Session, user_id: uuid.UUID, name: str) -> Portfolio:
    return PortfolioRepository(db).create(user_id, name)


def get_owned_portfolio(db: Session, user_id: uuid.UUID, portfolio_id: uuid.UUID) -> Portfolio:
    portfolio = PortfolioRepository(db).get(user_id, portfolio_id)
    if portfolio is None:
        raise NotFoundError(f"portfolio {portfolio_id} not found")
    return portfolio


def record_trade(
    db: Session, user_id: uuid.UUID, portfolio_id: uuid.UUID, data: TradeCreate
) -> Trade:
    get_owned_portfolio(db, user_id, portfolio_id)  # ownership check
    asset = MarketDataService(db).get_or_create_asset(data.symbol)

    trade = Trade(
        portfolio_id=portfolio_id,
        asset_id=asset.id,
        trade_type=data.trade_type,
        quantity=data.quantity,
        price=data.price,
        fees=data.fees,
        trade_date=data.trade_date,
    )
    return PortfolioRepository(db).add_trade(trade)


def get_portfolio_summary(
    db: Session, user_id: uuid.UUID, portfolio_id: uuid.UUID
) -> PortfolioSummary:
    get_owned_portfolio(db, user_id, portfolio_id)
    holdings, assets_by_id = _holdings_and_assets(db, portfolio_id)

    market_data = MarketDataService(db)
    asset_ids = list(holdings.keys())
    current_prices = {
        asset_id: price
        for asset_id in asset_ids
        if (price := market_data.get_latest_price(assets_by_id[asset_id])) is not None
    }

    valuations = value_holdings(holdings, current_prices)

    positions = [
        PositionRead(
            symbol=assets_by_id[v.asset_id].symbol,
            quantity=v.quantity,
            avg_cost=v.avg_cost,
            cost_basis=v.cost_basis,
            current_price=v.current_price,
            market_value=v.market_value,
            unrealized_pl=v.unrealized_pl,
            realized_pl=v.realized_pl,
        )
        for v in valuations
    ]

    # Realized P/L includes fully-closed positions too, so sum it from
    # `holdings` (every asset ever traded), not just currently-open `positions`.
    total_realized_pl = sum((h.realized_pl for h in holdings.values()), Decimal("0"))

    return PortfolioSummary(
        portfolio_id=portfolio_id,
        positions=positions,
        total_market_value=sum((p.market_value for p in positions), Decimal("0")),
        total_cost_basis=sum((p.cost_basis for p in positions), Decimal("0")),
        total_unrealized_pl=sum((p.unrealized_pl for p in positions), Decimal("0")),
        total_realized_pl=total_realized_pl,
    )


def get_portfolio_risk(
    db: Session,
    user_id: uuid.UUID,
    portfolio_id: uuid.UUID,
    lookback_days: int = 252,
    risk_free_rate: float = 0.0,
) -> PortfolioRisk:
    """Risk metrics over the trailing `lookback_days`, using *current*
    holdings' quantities applied across the whole window.

    LIMITATION, stated plainly: this treats today's position sizes as if
    they were held for the entire lookback period, not the actual
    (possibly different) sizes held on each historical day. A portfolio
    that doubled its AAPL position last week will have last month's
    volatility computed as if today's larger position existed then too.
    A fully trade-aware version would replay the exact position size held
    on each historical date — meaningfully more complex, and out of scope
    here. This is a common simplification in lightweight portfolio tools,
    not a hidden bug; it's called out here and in the API response.
    """
    get_owned_portfolio(db, user_id, portfolio_id)
    holdings, assets_by_id = _holdings_and_assets(db, portfolio_id)
    open_holdings = {aid: h for aid, h in holdings.items() if h.quantity > 0}

    if not open_holdings:
        return PortfolioRisk(
            portfolio_id=portfolio_id,
            lookback_days=lookback_days,
            date_from=None,
            date_to=None,
            annualized_volatility=None,
            sharpe_ratio=None,
            max_drawdown=None,
            cumulative_return=None,
            correlation_matrix={},
            warning="No open positions to assess.",
        )

    end = date_.today()
    start = end - timedelta(days=lookback_days)
    market_data = MarketDataService(db)

    price_series: dict[uuid.UUID, dict[date_, Decimal]] = {}
    for asset_id in open_holdings:
        history = market_data.get_history(assets_by_id[asset_id], start, end)
        price_series[asset_id] = dict(history)

    common_dates = sorted(set.intersection(*(set(s.keys()) for s in price_series.values())))
    warning = None
    if len(common_dates) < 20:
        warning = (
            f"Only {len(common_dates)} overlapping trading days of price history available; "
            "risk metrics based on very short histories are unreliable."
        )

    portfolio_values = [
        float(sum(open_holdings[aid].quantity * price_series[aid][d] for aid in open_holdings))
        for d in common_dates
    ]

    returns = daily_returns(portfolio_values)

    per_asset_returns = {}
    for asset_id in open_holdings:
        prices = [float(price_series[asset_id][d]) for d in common_dates]
        asset_returns = daily_returns(prices)
        if asset_returns.size > 0:
            per_asset_returns[assets_by_id[asset_id].symbol] = asset_returns

    correlations = (
        correlation_matrix(per_asset_returns) if len(per_asset_returns) >= 2 else {}
    )
    cumulative = cumulative_returns(returns) if returns.size > 0 else np.array([])

    return PortfolioRisk(
        portfolio_id=portfolio_id,
        lookback_days=lookback_days,
        date_from=common_dates[0] if common_dates else None,
        date_to=common_dates[-1] if common_dates else None,
        annualized_volatility=annualized_volatility(returns),
        sharpe_ratio=sharpe_ratio(returns, risk_free_rate),
        max_drawdown=max_drawdown(portfolio_values),
        cumulative_return=float(cumulative[-1]) if cumulative.size > 0 else None,
        correlation_matrix=correlations,
        warning=warning,
    )
