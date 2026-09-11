import uuid

from sqlalchemy.orm import Session

from app.models.category import Category
from app.repositories.category_repository import CategoryRepository


def list_categories(db: Session, user_id: uuid.UUID) -> list[Category]:
    return CategoryRepository(db).list_for_user(user_id)


def create_category(db: Session, user_id: uuid.UUID, name: str) -> Category:
    return CategoryRepository(db).create(user_id, name)


def seed_default_categories(db: Session, user_id: uuid.UUID) -> None:
    CategoryRepository(db).seed_defaults(user_id)
