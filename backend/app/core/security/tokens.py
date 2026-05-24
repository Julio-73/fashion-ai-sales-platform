import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from jose import JWTError, jwt
from pydantic import BaseModel

from app.core.config import get_settings
from app.core.errors import AppError


class TokenPayload(BaseModel):
    sub: UUID
    empresa_id: UUID
    roles: list[str]
    permissions: list[str]
    jti: str
    typ: str
    iss: str
    aud: str
    exp: int
    iat: int


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshTokenValue(BaseModel):
    token: str
    token_hash: str
    family_id: UUID
    expires_at: datetime


def create_access_token(
    *,
    user_id: UUID,
    empresa_id: UUID,
    roles: list[str],
    permissions: list[str],
) -> str:
    settings = get_settings()
    now = datetime.now(UTC)
    expires_at = now + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {
        "sub": str(user_id),
        "empresa_id": str(empresa_id),
        "roles": roles,
        "permissions": permissions,
        "jti": str(uuid4()),
        "typ": "access",
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(*, family_id: UUID | None = None) -> RefreshTokenValue:
    settings = get_settings()
    token = secrets.token_urlsafe(64)
    return RefreshTokenValue(
        token=token,
        token_hash=hash_refresh_token(token),
        family_id=family_id or uuid4(),
        expires_at=datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days),
    )


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def verify_access_token(token: str) -> TokenPayload:
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
            issuer=settings.jwt_issuer,
            audience=settings.jwt_audience,
        )
        parsed = TokenPayload.model_validate(payload)
    except (JWTError, ValueError) as exc:
        raise AppError(code="invalid_token", message="Invalid authentication token", status_code=401) from exc

    if parsed.typ != "access":
        raise AppError(code="invalid_token_type", message="Invalid authentication token", status_code=401)
    return parsed
