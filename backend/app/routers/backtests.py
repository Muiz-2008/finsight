from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.backtest import BacktestRequest, BacktestResponse
from app.services.backtest_service import run_moving_average_backtest

router = APIRouter(prefix="/api/v1/backtests", tags=["backtests"])


@router.post("", response_model=BacktestResponse)
def create_backtest(
    request: BacktestRequest,
    current_user: User = Depends(get_current_user),  # any authenticated user may run one
    db: Session = Depends(get_db),
) -> BacktestResponse:
    """Runs synchronously and returns the result directly — not persisted.
    Saving/listing past runs (GET /backtests/{id}) is a natural next step
    but adds a new table and history semantics beyond this project's
    current scope; noted as a future improvement rather than built half-way.
    """
    return run_moving_average_backtest(db, request)
