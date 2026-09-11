import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.portfolio import (
    PortfolioCreate,
    PortfolioRead,
    PortfolioSummary,
    TradeCreate,
    TradeRead,
)
from app.schemas.risk import PortfolioRisk
from app.services import portfolio_service

router = APIRouter(prefix="/api/v1/portfolios", tags=["portfolios"])


@router.get("", response_model=list[PortfolioRead])
def list_my_portfolios(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[PortfolioRead]:
    return portfolio_service.list_portfolios(db, current_user.id)


@router.post("", response_model=PortfolioRead, status_code=status.HTTP_201_CREATED)
def create_my_portfolio(
    data: PortfolioCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PortfolioRead:
    return portfolio_service.create_portfolio(db, current_user.id, data.name)


@router.post(
    "/{portfolio_id}/trades", response_model=TradeRead, status_code=status.HTTP_201_CREATED
)
def record_trade(
    portfolio_id: uuid.UUID,
    data: TradeCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TradeRead:
    return portfolio_service.record_trade(db, current_user.id, portfolio_id, data)


@router.get("/{portfolio_id}/performance", response_model=PortfolioSummary)
def portfolio_performance(
    portfolio_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PortfolioSummary:
    return portfolio_service.get_portfolio_summary(db, current_user.id, portfolio_id)


@router.get("/{portfolio_id}/risk", response_model=PortfolioRisk)
def portfolio_risk(
    portfolio_id: uuid.UUID,
    lookback_days: int = 252,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PortfolioRisk:
    return portfolio_service.get_portfolio_risk(db, current_user.id, portfolio_id, lookback_days)
