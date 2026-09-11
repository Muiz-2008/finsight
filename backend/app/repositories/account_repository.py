import uuid

from sqlalchemy.orm import Session

from app.models.account import Account, AccountType


class AccountRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def list_for_user(self, user_id: uuid.UUID) -> list[Account]:
        return (
            self._db.query(Account)
            .filter(Account.user_id == user_id)
            .order_by(Account.created_at)
            .all()
        )

    def get(self, user_id: uuid.UUID, account_id: uuid.UUID) -> Account | None:
        return (
            self._db.query(Account)
            .filter(Account.user_id == user_id, Account.id == account_id)
            .first()
        )

    def create(
        self, user_id: uuid.UUID, name: str, account_type: AccountType, currency: str
    ) -> Account:
        account = Account(user_id=user_id, name=name, account_type=account_type, currency=currency)
        self._db.add(account)
        self._db.commit()
        self._db.refresh(account)
        return account
