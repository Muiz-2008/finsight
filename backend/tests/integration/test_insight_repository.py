import uuid

from app.repositories.insight_repository import InsightRepository
from app.repositories.user_repository import UserRepository


def _make_user(db_session):
    return UserRepository(db_session).create(
        email=f"{uuid.uuid4()}@example.com", hashed_password="x", full_name=None
    )


def test_create_many_skips_a_message_identical_to_a_recent_one(db_session):
    user = _make_user(db_session)
    repo = InsightRepository(db_session)

    first = repo.create_many(user.id, "savings", ["Your savings rate increased from 22% to 29%."])
    second = repo.create_many(user.id, "savings", ["Your savings rate increased from 22% to 29%."])

    assert len(first) == 1
    assert len(second) == 0
    assert len(repo.list_for_user(user.id)) == 1


def test_create_many_still_inserts_a_genuinely_new_message(db_session):
    user = _make_user(db_session)
    repo = InsightRepository(db_session)

    repo.create_many(user.id, "spending", ["Transport spending increased 31%."])
    second = repo.create_many(user.id, "spending", ["Dining spending decreased 20%."])

    assert len(second) == 1
    assert len(repo.list_for_user(user.id)) == 2
