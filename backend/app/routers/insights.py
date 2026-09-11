from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.insight import InsightRead
from app.services.insight_service import generate_insights

router = APIRouter(prefix="/api/v1/insights", tags=["insights"])


@router.get("", response_model=list[InsightRead])
def get_my_insights(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[InsightRead]:
    """Recomputes every rule from current data and returns the fresh set —
    see app/services/insight_service.py for why this isn't cached.
    """
    return generate_insights(db, current_user.id)
