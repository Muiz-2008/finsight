import uuid
from decimal import Decimal

from sqlalchemy.orm import Session

from app.analytics.portfolio import TradeRecord, compute_holdings, value_holdings
from app.market_data.service import MarketDataService
from app.models.asset import Asset
from app.models.portfolio import Portfolio
from app.models.trade import Trade
from app.repositories.portfolio_repository import PortfolioRepository
from app.schemas.portfolio import PortfolioSummary, PositionRead, TradeCreate
from app.services.exceptions import NotFoundError


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
    repo = PortfolioRepository(db)
    trades = repo.list_trades(portfolio_id)

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

    market_data = MarketDataService(db)
    asset_ids = list(holdings.keys())
    assets_by_id: dict[uuid.UUID, Asset] = {
        a.id: a for a in db.query(Asset).filter(Asset.id.in_(asset_ids)).all()
    }
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
