"""generate_insights() must return the user's current insight history, not
just whatever it happened to insert on this call — InsightRepository.
create_many (see its own tests) skips inserting a message identical to a
recent one, so a naive "return what I just saved" would make GET
/insights return fewer results (even an empty list) on a repeat call with
unchanged underlying data, even though the earlier insight is still valid.
"""

import uuid

from app.repositories.insight_repository import InsightRepository
from app.repositories.user_repository import UserRepository
from app.services.insight_service import generate_insights


def test_generate_insights_still_returns_a_preexisting_insight_with_no_new_data(db_session):
    user = UserRepository(db_session).create(
        email=f"{uuid.uuid4()}@example.com", hashed_password="x", full_name=None
    )
    InsightRepository(db_session).create_many(
        user.id, "savings", ["Your savings rate increased from 22% to 29%."]
    )

    # No transactions/budgets/portfolios exist for this user, so every
    # rule in insight_service produces zero new messages this call.
    result = generate_insights(db_session, user.id)

    assert len(result) == 1
    assert result[0].message == "Your savings rate increased from 22% to 29%."
