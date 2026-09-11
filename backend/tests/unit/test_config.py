from app.config import Settings


def test_bare_postgresql_scheme_gets_psycopg_driver_added():
    settings = Settings(secret_key="x", database_url="postgresql://user:pass@host:5432/db")

    assert settings.database_url == "postgresql+psycopg://user:pass@host:5432/db"


def test_legacy_postgres_scheme_gets_psycopg_driver_added():
    # Heroku-style providers historically used the "postgres://" scheme.
    settings = Settings(secret_key="x", database_url="postgres://user:pass@host:5432/db")

    assert settings.database_url == "postgresql+psycopg://user:pass@host:5432/db"


def test_already_qualified_driver_is_left_alone():
    settings = Settings(secret_key="x", database_url="postgresql+psycopg://user:pass@host:5432/db")

    assert settings.database_url == "postgresql+psycopg://user:pass@host:5432/db"
