"""Capa de seguridad del módulo Admin Enterprise (aditiva).

No modifica ``app/core/security/*``. Define un ``AdminContext`` propio,
un emisor de JWT específico (sin ``empresa_id``) y un guardia
``require_admin()``.
"""
from __future__ import annotations

import hashlib
import secrets
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.core.errors import AppError

from app.modules.admin.models import SUPER_ADMIN_ROLE, AdminUser

# Las dependencias /auth siguen siendo el mismo bearer — solo cambia la
# validación de la claim ``typ`` para distinguir tokens de admin.
bearer_scheme = HTTPBearer(auto_error=False)

ADMIN_TOKEN_TYPE: str = "admin_access"
ADMIN_TOKEN_AUDIENCE: str = "ai-sales-agent-admin"
ADMIN_TOKEN_ISSUER: str = "ai-sales-agent-saas"

# Permisos que el módulo Admin define internamente (no choca con los del
# módulo auth/empresas porque son strings nuevos).
ADMIN_PERMISSIONS: dict[str, set[str]] = {
    "super_admin": {
        "admin:auth:me",
        "admin:tenants:read",
        "admin:tenants:write",
        "admin:tenants:suspend",
        "admin:tenants:activate",
        "admin:dashboard:read",
        "admin:audit:read",
    },
    "company_admin": {
        "admin:auth:me",
        "admin:tenants:read",
        "admin:dashboard:read",
        "admin:audit:read",
    },
    "agent": {
        "admin:auth:me",
    },
}


class AdminContext(BaseModel):
    """Contexto de un Admin autenticado. NO tiene ``empresa_id``."""

    user_id: UUID
    email: str
    roles: list[str]
    permissions: set[str]
    is_super_admin: bool

    def has_permission(self, permission: str) -> bool:
        return permission in self.permissions


class AdminTokenPayload(BaseModel):
    """Payload de un JWT emitido por el módulo Admin.

    Es un modelo paralelo a ``TokenPayload`` (que requiere ``empresa_id``).
    """

    sub: UUID
    email: str
    roles: list[str]
    permissions: list[str]
    jti: str
    typ: str = ADMIN_TOKEN_TYPE
    iss: str = ADMIN_TOKEN_ISSUER
    aud: str = ADMIN_TOKEN_AUDIENCE
    exp: int
    iat: int


# ─────────────────────────────────────────────────────────────────────────────
# JWT helpers (paralelos a ``app.core.security.tokens``, sin empresa_id)
# ─────────────────────────────────────────────────────────────────────────────


def _permissions_for_roles(roles: list[str]) -> set[str]:
    perms: set[str] = set()
    for role in roles:
        perms.update(ADMIN_PERMISSIONS.get(role, set()))
    return perms


def create_admin_access_token(*, user_id: UUID, email: str, roles: list[str]) -> str:
    settings = get_settings()
    now = datetime.now(UTC)
    expires_at = now + timedelta(minutes=settings.access_token_expire_minutes)
    permissions = sorted(_permissions_for_roles(roles))
    payload = {
        "sub": str(user_id),
        "email": email,
        "roles": roles,
        "permissions": permissions,
        "jti": str(uuid4()),
        "typ": ADMIN_TOKEN_TYPE,
        "iss": ADMIN_TOKEN_ISSUER,
        "aud": ADMIN_TOKEN_AUDIENCE,
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def verify_admin_access_token(token: str) -> AdminTokenPayload:
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
            issuer=ADMIN_TOKEN_ISSUER,
            audience=ADMIN_TOKEN_AUDIENCE,
        )
        parsed = AdminTokenPayload.model_validate(payload)
    except (JWTError, ValueError) as exc:
        raise AppError(code="invalid_token", message="Invalid admin token", status_code=401) from exc

    if parsed.typ != ADMIN_TOKEN_TYPE:
        raise AppError(
            code="invalid_token_type", message="Invalid admin token type", status_code=401
        )
    return parsed


def hash_admin_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_admin_refresh_token() -> tuple[str, str, UUID, datetime]:
    """Genera un refresh token opaco. Retorna (token, token_hash, family_id, expires_at)."""
    settings = get_settings()
    token = secrets.token_urlsafe(64)
    return (
        token,
        hash_admin_refresh_token(token),
        uuid4(),
        datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days),
    )


# ─────────────────────────────────────────────────────────────────────────────
# Dependency / Guard
# ─────────────────────────────────────────────────────────────────────────────


def _context_from_token(token: str) -> AdminContext:
    payload = verify_admin_access_token(token)
    permissions = set(payload.permissions)
    return AdminContext(
        user_id=payload.sub,
        email=payload.email,
        roles=payload.roles,
        permissions=permissions,
        is_super_admin=SUPER_ADMIN_ROLE in payload.roles,
    )


async def get_admin_context(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> AdminContext:
    """Devuelve el ``AdminContext`` a partir del bearer token.

    No toca ``app.core.security.dependencies`` — solo lee tokens cuyo
    ``typ == "admin_access"``.
    """
    if credentials is None:
        raise AppError(
            code="not_authenticated", message="Authentication required", status_code=401
        )
    return _context_from_token(credentials.credentials)


def require_admin() -> Callable[..., AdminContext]:
    """Guardia: cualquier Admin autenticado (super_admin, company_admin, agent)."""

    async def dependency(
        ctx: Annotated[AdminContext, Depends(get_admin_context)],
    ) -> AdminContext:
        return ctx

    return dependency


def require_admin_permission(permission: str) -> Callable[..., AdminContext]:
    """Guardia con verificación de permiso específico del módulo Admin."""

    async def dependency(
        ctx: Annotated[AdminContext, Depends(get_admin_context)],
    ) -> AdminContext:
        if permission not in ctx.permissions:
            raise AppError(
                code="permission_denied",
                message=f"Missing admin permission: {permission}",
                status_code=403,
            )
        return ctx

    return dependency


def require_super_admin() -> Callable[..., AdminContext]:
    """Guardia: solo ``super_admin`` puede pasar."""

    async def dependency(
        ctx: Annotated[AdminContext, Depends(get_admin_context)],
    ) -> AdminContext:
        if not ctx.is_super_admin:
            raise AppError(
                code="super_admin_required",
                message="Super admin role required",
                status_code=403,
            )
        return ctx

    return dependency


def build_admin_context_from_user(*, user: AdminUser) -> AdminContext:
    """Helper de testing / seed: construye un ``AdminContext`` desde un modelo ORM."""
    roles = [user.rol] if user.rol else []
    return AdminContext(
        user_id=user.id,
        email=user.email,
        roles=roles,
        permissions=_permissions_for_roles(roles),
        is_super_admin=SUPER_ADMIN_ROLE in roles,
    )


__all__ = [
    "ADMIN_TOKEN_AUDIENCE",
    "ADMIN_TOKEN_ISSUER",
    "ADMIN_TOKEN_TYPE",
    "AdminContext",
    "AdminTokenPayload",
    "build_admin_context_from_user",
    "create_admin_access_token",
    "create_admin_refresh_token",
    "get_admin_context",
    "hash_admin_refresh_token",
    "require_admin",
    "require_admin_permission",
    "require_super_admin",
    "verify_admin_access_token",
]
