from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    """Liveness check: is the process up? Does not touch the database."""
    return {"status": "ok"}


@router.get("/health/db")
def health_db(response: Response, db: Session = Depends(get_db)) -> dict[str, str]:
    """Readiness check: can we actually reach Postgres?

    Kept separate from /health on purpose — a load balancer or orchestrator
    should be able to tell "process alive but DB unreachable" apart from
    "process dead", since the correct response differs (don't restart the
    process for a DB outage it can't fix). Returns 503 on failure so the
    status code alone is enough for a health checker, without parsing the body.
    """
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "reachable"}
    except Exception as exc:  # noqa: BLE001 - deliberately broad: any DB failure -> unhealthy
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "error", "database": "unreachable", "detail": str(exc)}
