from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import health


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

    app.include_router(health.router)

    return app


app = create_app()
