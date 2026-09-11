import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import get_settings
from app.database import Base, get_db
from app.main import app


@pytest.fixture(scope="session")
def engine():
    """One engine per test session, pointed at DATABASE_URL.

    Requires a real, reachable Postgres — these are integration tests by
    design. Locally: `docker compose up postgres` first. In CI: a
    Postgres service container (see .github/workflows/ci.yml).
    """
    engine = create_engine(get_settings().database_url)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def db_session(engine):
    """A fresh session per test, with every table truncated afterward.

    Simpler than nested SAVEPOINT rollback (the other common pattern) and
    easy to reason about, at the cost of a delete-all per test rather than
    an in-memory rollback — a fine trade-off at this test count.
    """
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    yield session
    session.close()
    with engine.begin() as connection:
        for table in reversed(Base.metadata.sorted_tables):
            connection.execute(table.delete())


@pytest.fixture
def client(db_session):
    """TestClient with the real get_db dependency swapped for the
    test session, so requests hit the same transaction the test controls.
    """

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()
