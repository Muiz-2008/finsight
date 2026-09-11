from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt

from app.config import get_settings


def create_access_token(subject: str, expires_delta: timedelta | None = None) -> str:
    """Issue a signed JWT.

    `subject` is the user's id (as a string) — by convention JWTs identify
    the principal in the "sub" claim. Nothing sensitive goes in the
    payload: the token is base64-encoded, not encrypted, so anyone holding
    it can read the claims. Its guarantee is *integrity* (the signature
    proves the server issued it and it hasn't been tampered with), not
    confidentiality.
    """
    settings = get_settings()
    expire = datetime.now(UTC) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    payload = {"sub": subject, "exp": expire, "iat": datetime.now(UTC)}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> str:
    """Verify a JWT's signature and expiry, returning the subject (user id).

    Raises jose.JWTError (via jwt.decode) if the signature is invalid, the
    token is expired, or it's malformed — callers turn that into a 401.
    """
    settings = get_settings()
    payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
    subject = payload.get("sub")
    if subject is None:
        raise JWTError("Token payload missing 'sub' claim")
    return subject
