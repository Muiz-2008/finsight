import uuid

from sqlalchemy.orm import Session

from app.models.account import Account, AccountType
from app.repositories.account_repository import AccountRepository
from app.services.exceptions import NotFoundError


def list_accounts(db: Session, user_id: uuid.UUID) -> list[Account]:
    return AccountRepository(db).list_for_user(user_id)


def create_account(
    db: Session, user_id: uuid.UUID, name: str, account_type: AccountType, currency: str
) -> Account:
    return AccountRepository(db).create(user_id, name, account_type, currency)


def get_owned_account(db: Session, user_id: uuid.UUID, account_id: uuid.UUID) -> Account:
    account = AccountRepository(db).get(user_id, account_id)
    if account is None:
        raise NotFoundError(f"account {account_id} not found")
    return account
