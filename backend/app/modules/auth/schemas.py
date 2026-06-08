from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    company_name: str = Field(min_length=2, max_length=160)
    company_slug: str = Field(min_length=2, max_length=120, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    email: EmailStr
    password: str = Field(
        min_length=10,
        max_length=128,
    )

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        if not any(c in "!@#$%^&*(),.?\":{}|<>_-" for c in v):
            raise ValueError("Password must contain at least one special character")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    empresa_id: UUID | None = None


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(min_length=32)


class LogoutRequest(BaseModel):
    refresh_token: str = Field(min_length=32)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class CurrentUserResponse(BaseModel):
    user_id: UUID
    empresa_id: UUID
    roles: list[str]
    permissions: set[str]

    model_config = ConfigDict(from_attributes=True)


class AuthSessionResponse(TokenResponse):
    user: CurrentUserResponse
