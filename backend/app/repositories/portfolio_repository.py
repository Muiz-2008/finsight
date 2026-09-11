import uuid

from sqlalchemy.orm import Session

from app.models.portfolio import Portfolio
from app.models.trade import Trade


class PortfolioRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def list_for_user(self, user_id: uuid.UUID) -> list[Portfolio]:
        return self._db.query(Portfolio).filter(Portfolio.user_id == user_id).all()

    def get(self, user_id: uuid.UUID, portfolio_id: uuid.UUID) -> Portfolio | None:
        return (
            self._db.query(Portfolio)
            .filter(Portfolio.user_id == user_id, Portfolio.id == portfolio_id)
            .first()
        )

    def create(self, user_id: uuid.UUID, name: str) -> Portfolio:
        portfolio = Portfolio(user_id=user_id, name=name)
        self._db.add(portfolio)
        self._db.commit()
        self._db.refresh(portfolio)
        return portfolio

    def list_trades(self, portfolio_id: uuid.UUID) -> list[Trade]:
        return (
            self._db.query(Trade)
            .filter(Trade.portfolio_id == portfolio_id)
            .order_by(Trade.trade_date, Trade.created_at)
            .all()
        )

    def add_trade(self, trade: Trade) -> Trade:
        self._db.add(trade)
        self._db.commit()
        self._db.refresh(trade)
        return trade
