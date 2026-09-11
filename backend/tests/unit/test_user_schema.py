import pytest
from pydantic import ValidationError

from app.schemas.user import UserCreate


def test_accepts_a_normal_ascii_password():
    user = UserCreate(email="a@example.com", password="correcthorsebatterystaple")

    assert user.password == "correcthorsebatterystaple"


def test_rejects_password_under_72_chars_but_over_72_bytes():
    # 72 four-byte emoji = 72 chars (passes Field max_length) but 288
    # bytes when UTF-8 encoded (fails bcrypt's actual limit).
    password = "\U0001f600" * 72
    assert len(password) == 72

    with pytest.raises(ValidationError):
        UserCreate(email="a@example.com", password=password)
