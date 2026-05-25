"""Tests for JWT tokens."""
from __future__ import annotations
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4
import pytest
from jose import jwt
from app.core.config import get_settings
from app.core.errors import AppError
from app.core.security.tokens import (
    RefreshTokenValue, TokenPayload, create_access_token,
    create_refresh_token, hash_refresh_token, verify_access_token,
)


class TestCreateAccessToken:
    def test_creates_valid_jwt(self):
        user_id = uuid4(); empresa_id = uuid4()
        roles = ["owner"]; permissions = ["customers:read"]
        token = create_access_token(user_id=user_id, empresa_id=empresa_id, roles=roles, permissions=permissions)
        settings = get_settings()
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm],
                             issuer=settings.jwt_issuer, audience=settings.jwt_audience)
        assert payload["sub"] == str(user_id)
        assert payload["empresa_id"] == str(empresa_id)
        assert payload["roles"] == roles
        assert payload["typ"] == "access"

    def test_expiration_time(self):
        user_id = uuid4(); empresa_id = uuid4()
        token = create_access_token(user_id=user_id, empresa_id=empresa_id, roles=["admin"], permissions=[])
        settings = get_settings()
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm],
                             issuer=settings.jwt_issuer, audience=settings.jwt_audience)
        expected = int((datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)).timestamp())
        assert abs(payload["exp"] - expected) <= 2


class TestVerifyAccessToken:
    def test_valid_token_returns_payload(self):
        token = create_access_token(user_id=uuid4(), empresa_id=uuid4(), roles=["sales_agent"], permissions=["customers:read"])
        payload = verify_access_token(token)
        assert isinstance(payload, TokenPayload)
        assert payload.typ == "access"

    def test_invalid_token_raises_error(self):
        with pytest.raises(AppError) as e:
            verify_access_token("invalid.token.here")
        assert e.value.status_code == 401

    def test_expired_token_raises_error(self):
        settings = get_settings()
        payload = {"sub": str(uuid4()), "empresa_id": str(uuid4()), "roles": [], "permissions": [],
                   "jti": str(uuid4()), "typ": "access", "iss": settings.jwt_issuer, "aud": settings.jwt_audience,
                   "iat": int((datetime.now(UTC) - timedelta(hours=2)).timestamp()),
                   "exp": int((datetime.now(UTC) - timedelta(hours=1)).timestamp())}
        token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
        with pytest.raises(AppError):
            verify_access_token(token)

    def test_refresh_token_type_rejected(self):
        settings = get_settings()
        payload = {"sub": str(uuid4()), "empresa_id": str(uuid4()), "roles": [], "permissions": [],
                   "jti": str(uuid4()), "typ": "refresh", "iss": settings.jwt_issuer, "aud": settings.jwt_audience,
                   "iat": int(datetime.now(UTC).timestamp()),
                   "exp": int((datetime.now(UTC) + timedelta(hours=1)).timestamp())}
        token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
        with pytest.raises(AppError) as e:
            verify_access_token(token)
        assert e.value.code == "invalid_token_type"


class TestCreateRefreshToken:
    def test_returns_refresh_token_value(self):
        result = create_refresh_token()
        assert isinstance(result, RefreshTokenValue)
        assert len(result.token) > 32
        assert result.token_hash == hash_refresh_token(result.token)

    def test_family_id_preserved_when_provided(self):
        family_id = uuid4()
        assert create_refresh_token(family_id=family_id).family_id == family_id


class TestHashRefreshToken:
    def test_consistent_hash(self):
        assert hash_refresh_token("abc") == hash_refresh_token("abc")

    def test_different_tokens_different_hashes(self):
        assert hash_refresh_token("a") != hash_refresh_token("b")
