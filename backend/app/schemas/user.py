import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    full_name: str | None = None

    @field_validator("password")
    @classmethod
    def password_must_fit_bcrypt_byte_limit(cls, value: str) -> str:
        # max_length=72 above counts *characters*, but bcrypt's limit is 72
        # *bytes* — a password full of multi-byte UTF-8 characters (e.g.
        # emoji, 4 bytes each) could pass the character check yet still
        # blow past the byte limit, crashing hash_password() with an
        # unhandled ValueError instead of a clean 422. Checked explicitly
        # here so it's a validation error, not a 500.
        if len(value.encode("utf-8")) > 72:
            raise ValueError("password must be at most 72 bytes when UTF-8 encoded")
        return value


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    full_name: str | None
    is_active: bool
    created_at: datetime
