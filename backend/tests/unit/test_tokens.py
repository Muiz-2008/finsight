from datetime import timedelta

import pytest
from jose import JWTError

from app.security.tokens import create_access_token, decode_access_token


def test_decode_returns_the_original_subject():
    token = create_access_token(subject="user-123")

    assert decode_access_token(token) == "user-123"


def test_decode_rejects_expired_token():
    token = create_access_token(subject="user-123", expires_delta=timedelta(seconds=-1))

    with pytest.raises(JWTError):
        decode_access_token(token)


def test_decode_rejects_tampered_token():
    token = create_access_token(subject="user-123")
    tampered = token[:-1] + ("A" if token[-1] != "A" else "B")

    with pytest.raises(JWTError):
        decode_access_token(tampered)
