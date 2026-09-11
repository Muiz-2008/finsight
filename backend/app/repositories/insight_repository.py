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
        rows = [Insight(user_id=user_id, category=category, message=m) for m in messages]
        self._db.add_all(rows)
        self._db.commit()
        for row in rows:
            self._db.refresh(row)
        return rows
