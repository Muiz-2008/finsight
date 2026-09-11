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
    # Flip a character in the middle of the signature, not the last one:
    # base64url's final symbol only encodes a partial byte (the trailing
    # bits are unused padding that decoding ignores), so roughly 1 in 4
    # replacement characters there decode to the *same* bytes and the
    # "tampered" token verifies anyway — a genuinely flaky assertion, not
    # a flaky test runner. A middle character always changes a full byte.
    mid = len(token) // 2
    tampered = token[:mid] + ("A" if token[mid] != "A" else "B") + token[mid + 1 :]

    with pytest.raises(JWTError):
        decode_access_token(tampered)
