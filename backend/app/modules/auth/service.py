import logging
import time
from uuid import UUID

from sqlalchemy.exc import IntegrityError

from app.core.config import get_settings
from app.core.errors import AppError
from app.core.redis import get_redis
from app.core.security.password import hash_password, verify_password
from app.core.security.permissions import permissions_for_roles
from app.core.security.tokens import (
    create_access_token,
    create_refresh_token,
    hash_refresh_token,
)
from app.modules.auth.models import EmpresaUsuario, Usuario
from app.modules.auth.repository import AuthRepository
from app.modules.auth.schemas import (
    AuthSessionResponse,
    CurrentUserResponse,
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    TokenResponse,
)

logger = logging.getLogger("ai_sales_agent.auth")

ACCOUNT_LOCKOUT_MAX_ATTEMPTS = 5
ACCOUNT_LOCKOUT_WINDOW = 300

_login_failures: dict[str, list[float]] = {}


async def _redis_lockout_key(email: str) -> str:
    return f"lockout:{email.lower()}"


async def _check_account_locked(email: str) -> None:
    now = time.time()
    r = await get_redis()
    if r is not None:
        try:
            key = await _redis_lockout_key(email)
            count = await r.llen(key)
            if count >= ACCOUNT_LOCKOUT_MAX_ATTEMPTS:
                oldest = await r.lindex(key, 0)
                if oldest:
                    remaining = int(ACCOUNT_LOCKOUT_WINDOW - (now - float(oldest)))
                    if remaining > 0:
                        raise AppError(
                            code="account_locked",
                            message=f"Account temporarily locked due to too many failed attempts. Try again in {remaining} seconds.",
                            status_code=429,
                        )
                    await r.delete(key)
        except AppError:
            raise
        except Exception:
            pass
    if email in _login_failures:
        _login_failures[email] = [t for t in _login_failures[email] if now - t < ACCOUNT_LOCKOUT_WINDOW]
        if len(_login_failures[email]) >= ACCOUNT_LOCKOUT_MAX_ATTEMPTS:
            remaining = int(ACCOUNT_LOCKOUT_WINDOW - (now - _login_failures[email][0]))
            raise AppError(
                code="account_locked",
                message=f"Account temporarily locked due to too many failed attempts. Try again in {remaining} seconds.",
                status_code=429,
            )


async def _record_login_failure(email: str) -> None:
    now = time.time()
    r = await get_redis()
    if r is not None:
        try:
            key = await _redis_lockout_key(email)
            pipe = r.pipeline()
            pipe.rpush(key, now)
            pipe.ltrim(key, -ACCOUNT_LOCKOUT_MAX_ATTEMPTS, -1)
            pipe.expire(key, ACCOUNT_LOCKOUT_WINDOW)
            await pipe.execute()
            return
        except Exception:
            pass
    if email not in _login_failures:
        _login_failures[email] = []
    _login_failures[email].append(now)


async def _clear_login_failures(email: str) -> None:
    r = await get_redis()
    if r is not None:
        try:
            key = await _redis_lockout_key(email)
            await r.delete(key)
            return
        except Exception:
            pass
    _login_failures.pop(email, None)


class AuthService:
    def __init__(self, repository: AuthRepository) -> None:
        self._repository = repository

    async def register(
        self, payload: RegisterRequest, *, ip_address: str | None = None
    ) -> AuthSessionResponse:
        password_hash = hash_password(payload.password)
        try:
            _, user, membership = await self._repository.create_company_with_owner(
                company_name=payload.company_name,
                company_slug=payload.company_slug,
                email=payload.email.lower(),
                password_hash=password_hash,
            )
            response = await self._create_session_response(user=user, membership=membership)
            await self._repository.commit()
            logger.info(
                "Registered user=%s company=%s ip=%s",
                user.id, membership.empresa_id, ip_address or "unknown",
            )
            return response
        except IntegrityError as exc:
            await self._repository.rollback()
            logger.warning("Registration conflict: %s", exc)
            raise AppError(
                code="registration_conflict",
                message="Company slug or email is already registered",
                status_code=409,
            ) from exc

    async def login(
        self, payload: LoginRequest, *, ip_address: str | None = None
    ) -> AuthSessionResponse:
        await _check_account_locked(payload.email.lower())
        user = await self._repository.get_user_by_email(email=payload.email.lower())
        if user is None or not verify_password(payload.password, user.password_hash):
            await _record_login_failure(payload.email.lower())
            logger.warning("Failed login attempt for email=%s", payload.email)
            raise AppError(code="invalid_credentials", message="Invalid email or password", status_code=401)

        if user.estado != "active":
            await _record_login_failure(payload.email.lower())
            logger.warning("Disabled account login attempt user=%s", user.id)
            raise AppError(code="account_disabled", message="Account is not active", status_code=403)

        await _clear_login_failures(payload.email.lower())
        membership = await self._resolve_membership(user_id=user.id, empresa_id=payload.empresa_id)
        response = await self._create_session_response(user=user, membership=membership)
        await self._repository.commit()
        logger.info(
            "Login success user=%s empresa=%s ip=%s",
            user.id, membership.empresa_id, ip_address or "unknown",
        )
        return response

    async def refresh(self, payload: RefreshTokenRequest) -> TokenResponse:
        token_hash = hash_refresh_token(payload.refresh_token)
        refresh_token = await self._repository.get_active_refresh_token(token_hash=token_hash)
        if refresh_token is None:
            stale_token = await self._repository.get_refresh_token_by_hash(token_hash=token_hash)
            if stale_token is not None:
                logger.warning("Reused refresh token detected, revoking family family=%s", stale_token.family_id)
                await self._repository.revoke_refresh_token_family(family_id=stale_token.family_id)
                await self._repository.commit()
            raise AppError(code="invalid_refresh_token", message="Invalid refresh token", status_code=401)

        membership = await self._repository.get_membership(
            empresa_id=refresh_token.empresa_id,
            usuario_id=refresh_token.usuario_id,
        )
        if membership is None:
            logger.warning("Refresh for invalid membership user=%s", refresh_token.usuario_id)
            await self._repository.revoke_refresh_token_family(family_id=refresh_token.family_id)
            await self._repository.commit()
            raise AppError(code="invalid_session", message="Session is no longer valid", status_code=401)

        rotated = create_refresh_token(family_id=refresh_token.family_id)
        new_record = await self._repository.create_refresh_token(
            empresa_id=refresh_token.empresa_id,
            usuario_id=refresh_token.usuario_id,
            token_hash=rotated.token_hash,
            family_id=rotated.family_id,
            expires_at=rotated.expires_at,
        )
        await self._repository.revoke_refresh_token(
            refresh_token=refresh_token,
            replaced_by_token_id=new_record.id,
        )

        roles = [membership.rol]
        permissions = permissions_for_roles(roles)
        access_token = create_access_token(
            user_id=refresh_token.usuario_id,
            empresa_id=refresh_token.empresa_id,
            roles=roles,
            permissions=permissions,
        )
        await self._repository.commit()

        return TokenResponse(
            access_token=access_token,
            refresh_token=rotated.token,
            expires_in=get_settings().access_token_expire_minutes * 60,
        )

    async def logout(self, payload: RefreshTokenRequest) -> None:
        refresh_token = await self._repository.get_refresh_token_by_hash(
            token_hash=hash_refresh_token(payload.refresh_token)
        )
        if refresh_token is not None and refresh_token.revoked_at is None:
            await self._repository.revoke_refresh_token(refresh_token=refresh_token)
            await self._repository.commit()

    async def _resolve_membership(
        self,
        *,
        user_id: UUID,
        empresa_id: UUID | None,
    ) -> EmpresaUsuario:
        if empresa_id is not None:
            membership = await self._repository.get_membership(empresa_id=empresa_id, usuario_id=user_id)
            if membership is None:
                raise AppError(code="tenant_access_denied", message="Tenant access denied", status_code=403)
            return membership

        memberships = await self._repository.list_active_memberships(usuario_id=user_id)
        if not memberships:
            raise AppError(code="tenant_access_denied", message="Tenant access denied", status_code=403)
        return memberships[0]

    async def _create_session_response(
        self,
        *,
        user: Usuario,
        membership: EmpresaUsuario,
    ) -> AuthSessionResponse:
        roles = [membership.rol]
        permissions = permissions_for_roles(roles)
        access_token = create_access_token(
            user_id=user.id,
            empresa_id=membership.empresa_id,
            roles=roles,
            permissions=permissions,
        )
        refresh = create_refresh_token()
        await self._repository.create_refresh_token(
            empresa_id=membership.empresa_id,
            usuario_id=user.id,
            token_hash=refresh.token_hash,
            family_id=refresh.family_id,
            expires_at=refresh.expires_at,
        )

        current_user = CurrentUserResponse(
            user_id=user.id,
            empresa_id=membership.empresa_id,
            roles=roles,
            permissions=set(permissions),
        )
        return AuthSessionResponse(
            access_token=access_token,
            refresh_token=refresh.token,
            expires_in=get_settings().access_token_expire_minutes * 60,
            user=current_user,
        )

