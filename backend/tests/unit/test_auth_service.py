"""Tests for AuthService."""
from __future__ import annotations
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
import pytest
from sqlalchemy.exc import IntegrityError
from app.core.config import get_settings
from app.core.errors import AppError
from app.core.security.password import hash_password
from app.modules.auth.models import Usuario, EmpresaUsuario, RefreshToken
from app.modules.auth.schemas import LoginRequest, RefreshTokenRequest, RegisterRequest

pytestmark = pytest.mark.asyncio


class TestRegister:
    async def test_registers_company_and_user(self, auth_service, auth_repository):
        payload = RegisterRequest(
            company_name="Test Company", company_slug="test-company",
            email="test@example.com", password="SecurePass123!",
        )
        mock_user = MagicMock(spec=Usuario); mock_user.id = uuid4()
        mock_membership = MagicMock(spec=EmpresaUsuario)
        mock_membership.empresa_id = uuid4(); mock_membership.rol = "owner"
        auth_repository.create_company_with_owner = AsyncMock(return_value=(MagicMock(), mock_user, mock_membership))
        auth_repository.create_refresh_token = AsyncMock()
        auth_repository.commit = AsyncMock()
        result = await auth_service.register(payload)
        assert result.access_token is not None
        assert result.refresh_token is not None
        assert result.token_type == "bearer"
        assert result.user.roles == ["owner"]
        auth_repository.commit.assert_awaited_once()

    async def test_duplicate_raises_409(self, auth_service, auth_repository):
        payload = RegisterRequest(
            company_name="Test", company_slug="test",
            email="dup@example.com", password="SecurePass123!",
        )
        auth_repository.create_company_with_owner = AsyncMock(side_effect=IntegrityError("mock", None, None))
        auth_repository.rollback = AsyncMock()
        with pytest.raises(AppError) as e:
            await auth_service.register(payload)
        assert e.value.status_code == 409
        assert e.value.code == "registration_conflict"


class TestLogin:
    async def test_valid_login_returns_session(self, auth_service, auth_repository):
        mock_user = MagicMock(spec=Usuario)
        mock_user.id = uuid4(); mock_user.email = "user@example.com"
        mock_user.password_hash = hash_password("AnyPass123!")
        mock_user.estado = "active"
        mock_membership = MagicMock(spec=EmpresaUsuario)
        mock_membership.empresa_id = uuid4(); mock_membership.rol = "sales_agent"
        auth_repository.get_user_by_email = AsyncMock(return_value=mock_user)
        auth_repository.get_membership = AsyncMock(return_value=mock_membership)
        auth_repository.create_refresh_token = AsyncMock()
        auth_repository.commit = AsyncMock()
        with patch("app.modules.auth.service.verify_password", return_value=True):
            result = await auth_service.login(LoginRequest(email="user@example.com", password="AnyPass123!", empresa_id=uuid4()))
            assert result.access_token is not None

    async def test_invalid_email_returns_401(self, auth_service, auth_repository):
        auth_repository.get_user_by_email = AsyncMock(return_value=None)
        with pytest.raises(AppError) as e:
            await auth_service.login(LoginRequest(email="x@y.com", password="AnyPass123!"))
        assert e.value.status_code == 401

    async def test_disabled_account_returns_403(self, auth_service, auth_repository):
        mock_user = MagicMock(spec=Usuario)
        mock_user.password_hash = hash_password("AnyPass123!")
        mock_user.estado = "inactive"; mock_user.id = uuid4()
        auth_repository.get_user_by_email = AsyncMock(return_value=mock_user)
        with patch("app.modules.auth.service.verify_password", return_value=True):
            with pytest.raises(AppError) as e:
                await auth_service.login(LoginRequest(email="d@d.com", password="AnyPass123!"))
            assert e.value.status_code == 403
            assert e.value.code == "account_disabled"


class TestRefreshToken:
    async def test_valid_refresh_rotates_token(self, auth_service, auth_repository):
        mock_r = MagicMock(spec=RefreshToken)
        mock_r.id = uuid4(); mock_r.empresa_id = uuid4()
        mock_r.usuario_id = uuid4(); mock_r.family_id = uuid4()
        mock_r.revoked_at = None
        mock_m = MagicMock(spec=EmpresaUsuario); mock_m.rol = "admin"
        auth_repository.get_active_refresh_token = AsyncMock(return_value=mock_r)
        auth_repository.get_membership = AsyncMock(return_value=mock_m)
        auth_repository.create_refresh_token = AsyncMock()
        auth_repository.revoke_refresh_token = AsyncMock()
        auth_repository.commit = AsyncMock()
        result = await auth_service.refresh(RefreshTokenRequest(refresh_token="v" * 32))
        assert result.access_token is not None
        auth_repository.revoke_refresh_token.assert_awaited_once()

    async def test_reused_token_revokes_family(self, auth_service, auth_repository):
        family_id = uuid4()
        stale = MagicMock(spec=RefreshToken)
        stale.family_id = family_id; stale.revoked_at = None
        from datetime import UTC, datetime
        stale.revoked_at = datetime.now(UTC)
        auth_repository.get_active_refresh_token = AsyncMock(return_value=None)
        auth_repository.get_refresh_token_by_hash = AsyncMock(return_value=stale)
        auth_repository.revoke_refresh_token_family = AsyncMock()
        auth_repository.commit = AsyncMock()
        with pytest.raises(AppError) as e:
            await auth_service.refresh(RefreshTokenRequest(refresh_token="r" * 32))
        assert e.value.status_code == 401
        auth_repository.revoke_refresh_token_family.assert_awaited_once_with(family_id=family_id)

    async def test_invalid_token_returns_401(self, auth_service, auth_repository):
        auth_repository.get_active_refresh_token = AsyncMock(return_value=None)
        auth_repository.get_refresh_token_by_hash = AsyncMock(return_value=None)
        with pytest.raises(AppError) as e:
            await auth_service.refresh(RefreshTokenRequest(refresh_token="i" * 32))
        assert e.value.status_code == 401


class TestLogout:
    async def test_logout_revokes_token(self, auth_service, auth_repository):
        mock_t = MagicMock(spec=RefreshToken); mock_t.revoked_at = None
        auth_repository.get_refresh_token_by_hash = AsyncMock(return_value=mock_t)
        auth_repository.revoke_refresh_token = AsyncMock()
        auth_repository.commit = AsyncMock()
        await auth_service.logout(RefreshTokenRequest(refresh_token="v" * 32))
        auth_repository.revoke_refresh_token.assert_awaited_once()

    async def test_logout_unknown_token_does_nothing(self, auth_service, auth_repository):
        auth_repository.get_refresh_token_by_hash = AsyncMock(return_value=None)
        auth_repository.revoke_refresh_token = AsyncMock()
        await auth_service.logout(RefreshTokenRequest(refresh_token="u" * 32))
        auth_repository.revoke_refresh_token.assert_not_called()
