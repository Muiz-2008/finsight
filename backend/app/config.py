from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration, sourced from environment variables / .env.

    Nothing here has a default that would work as a *production* secret —
    SECRET_KEY has no default at all, so the app refuses to start without
    one being supplied explicitly.
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    environment: str = "development"

    database_url: str = "postgresql+psycopg://finsight:finsight@localhost:5432/finsight"

    secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    cors_origins: list[str] = ["http://localhost:5173"]

    # "local": deterministic synthetic prices, no network — the default,
    # since it's what makes tests/CI/demos reproducible without a live API.
    # "yfinance": real (free, unofficial) market data — set this in
    # production via env var. See app/market_data/.
    market_data_provider: str = "local"


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance.

    lru_cache turns this into a singleton: Settings() (which reads env vars
    and the .env file) runs once per process, not on every request.
    """
    return Settings()
