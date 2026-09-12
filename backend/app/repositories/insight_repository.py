import uuid

from sqlalchemy.orm import Session

from app.models.insight import Insight


class InsightRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def list_for_user(self, user_id: uuid.UUID, limit: int = 50) -> list[Insight]:
        return (
            self._db.query(Insight)
            .filter(Insight.user_id == user_id)
            .order_by(Insight.created_at.desc())
            .limit(limit)
            .all()
        )

    def create_many(self, user_id: uuid.UUID, category: str, messages: list[str]) -> list[Insight]:
        """Skips any message identical to one already among this user's
        most recent insights. Without this, GET /insights (which
        regenerates from live data on every call — see insight_service.
        generate_insights) would insert the exact same sentence again
        every time a caller hit it with unchanged underlying data, e.g.
        the Dashboard and Insights pages both loading it back to back —
        real, unbounded row growth from routine navigation, not new
        information.
        """
        recent_texts = {
            text
            for (text,) in self._db.query(Insight.message)
            .filter(Insight.user_id == user_id)
            .order_by(Insight.created_at.desc())
            .limit(20)
            .all()
        }
        new_messages = [m for m in messages if m not in recent_texts]
        if not new_messages:
            return []

        rows = [Insight(user_id=user_id, category=category, message=m) for m in new_messages]
        self._db.add_all(rows)
        self._db.commit()
        for row in rows:
            self._db.refresh(row)
        return rows
