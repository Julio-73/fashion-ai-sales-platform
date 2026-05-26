from collections.abc import Callable
from typing import Annotated

from fastapi import Depends

from app.core.errors import AppError
from app.core.security.dependencies import TenantContext, get_tenant_context

ROLE_PERMISSIONS: dict[str, set[str]] = {
    "owner": {
        "auth:me",
        "customers:read",
        "customers:write",
        "products:read",
        "products:write",
        "chats:read",
        "chats:write",
        "conversations:read",
        "conversations:write",
        "analytics:read",
        "settings:manage",
        "users:manage",
        "sales:read",
    },
    "admin": {
        "auth:me",
        "customers:read",
        "customers:write",
        "products:read",
        "products:write",
        "chats:read",
        "chats:write",
        "conversations:read",
        "conversations:write",
        "analytics:read",
        "settings:manage",
        "sales:read",
    },
    "sales_agent": {
        "auth:me",
        "customers:read",
        "customers:write",
        "products:read",
        "chats:read",
        "chats:write",
        "conversations:read",
        "conversations:write",
        "sales:read",
    },
    "analyst": {
        "auth:me",
        "customers:read",
        "products:read",
        "conversations:read",
        "analytics:read",
        "sales:read",
    },
}


def permissions_for_roles(roles: list[str]) -> list[str]:
    permissions: set[str] = set()
    for role in roles:
        permissions.update(ROLE_PERMISSIONS.get(role, set()))
    return sorted(permissions)


def require_permission(permission: str) -> Callable[..., TenantContext]:
    async def dependency(
        tenant: Annotated[TenantContext, Depends(get_tenant_context)],
    ) -> TenantContext:
        if permission not in tenant.permissions:
            raise AppError(code="permission_denied", message="Permission denied", status_code=403)
        return tenant

    return dependency
