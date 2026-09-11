from datetime import date as date_
from datetime import timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.analytics import (
    BudgetComparison,
    CashflowSummary,
    MonthlyCashflowPoint,
    SpendingSummary,
)
from app.schemas.anomaly import AnomalyRead
from app.services import analytics_service, anomaly_service

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])


def _default_range(date_from: date_ | None, date_to: date_ | None) -> tuple[date_, date_]:
    end = date_to or date_.today()
    start = date_from or (end - timedelta(days=30))
    return start, end


@router.get("/cashflow", response_model=CashflowSummary)
def cashflow(
    date_from: date_ | None = Query(default=None),
    date_to: date_ | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CashflowSummary:
    start, end = _default_range(date_from, date_to)
    return analytics_service.get_cashflow_summary(db, current_user.id, start, end)


@router.get("/cashflow/monthly", response_model=list[MonthlyCashflowPoint])
def cashflow_monthly(
    date_from: date_ | None = Query(default=None),
    date_to: date_ | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[MonthlyCashflowPoint]:
    start, end = _default_range(date_from, date_to)
    return analytics_service.get_monthly_cashflow(db, current_user.id, start, end)


@router.get("/spending", response_model=SpendingSummary)
def spending(
    date_from: date_ | None = Query(default=None),
    date_to: date_ | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SpendingSummary:
    start, end = _default_range(date_from, date_to)
    return analytics_service.get_spending_summary(db, current_user.id, start, end)


@router.get("/budgets", response_model=list[BudgetComparison])
def budget_comparison(
    date_from: date_ | None = Query(default=None),
    date_to: date_ | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[BudgetComparison]:
    start, end = _default_range(date_from, date_to)
    return analytics_service.get_budget_comparison(db, current_user.id, start, end)


@router.get("/anomalies", response_model=list[AnomalyRead])
def anomalies(
    method: str = Query(default="zscore", pattern="^(zscore|iqr)$"),
    lookback_days: int = Query(default=180, ge=7, le=730),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[AnomalyRead]:
    return anomaly_service.detect_spending_anomalies(db, current_user.id, method, lookback_days)
