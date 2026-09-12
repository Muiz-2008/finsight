from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.routers import (
    accounts,
    analytics,
    assets,
    auth,
    backtests,
    budgets,
    categories,
    health,
    insights,
    portfolios,
    transactions,
    users,
)
from app.services.exceptions import NotFoundError, ValidationError


def create_app() -> FastAPI:
    """Application factory.

    Building the app in a function (rather than at module scope) means
    tests can construct fresh app instances with different settings/
    overridden dependencies instead of sharing one global object.
    """
    settings = get_settings()

    app = FastAPI(
        title="FinSight API",
        description="Financial analytics, portfolio intelligence and risk platform",
        version="0.1.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Centralized so every router raises plain domain exceptions
    # (NotFoundError, ValidationError) instead of importing FastAPI just to
    # construct an HTTPException — keeps the service layer framework-free.
    @app.exception_handler(NotFoundError)
    async def not_found_handler(request: Request, exc: NotFoundError) -> JSONResponse:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": str(exc)})

    @app.exception_handler(ValidationError)
    async def validation_error_handler(request: Request, exc: ValidationError) -> JSONResponse:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"detail": str(exc)})

    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(users.router)
    app.include_router(accounts.router)
    app.include_router(assets.router)
    app.include_router(categories.router)
    app.include_router(transactions.router)
    app.include_router(budgets.router)
    app.include_router(portfolios.router)
    app.include_router(analytics.router)
    app.include_router(insights.router)
    app.include_router(backtests.router)

    return app


app = create_app()
