import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.security.tokens import decode_access_token

# tokenUrl only tells Swagger UI where to POST for a token when you use its
# "Authorize" button — it doesn't affect actual token verification below.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """Resolve the bearer token on every protected request into a User row.

    This is the authorization boundary: any router that depends on this
    function is guaranteed a real, active user before its body runs — the
    route itself never has to think about "is this token valid".
    """
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        subject = decode_access_token(token)
        user_id = uuid.UUID(subject)
    except (JWTError, ValueError) as exc:
        raise credentials_error from exc

    user = UserRepository(db).get_by_id(user_id)
    if user is None:
        raise credentials_error
    return user
