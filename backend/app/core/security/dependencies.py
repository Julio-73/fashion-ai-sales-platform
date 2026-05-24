from typing import Annotated
from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from app.core.errors import AppError
from app.core.security.tokens import TokenPayload, verify_access_token

bearer_scheme = HTTPBearer(auto_error=False)


class AuthenticatedUser(BaseModel):
    user_id: UUID
    empresa_id: UUID
    roles: list[str]
    permissions: set[str]


class TenantContext(BaseModel):
    empresa_id: UUID
    user_id: UUID
    roles: list[str]
    permissions: set[str]


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> AuthenticatedUser:
    if credentials is None:
        raise AppError(code="not_authenticated", message="Authentication required", status_code=401)

    payload: TokenPayload = verify_access_token(credentials.credentials)
    return AuthenticatedUser(
        user_id=payload.sub,
        empresa_id=payload.empresa_id,
        roles=payload.roles,
        permissions=set(payload.permissions),
    )


async def get_tenant_context(
    user: Annotated[AuthenticatedUser, Depends(get_current_user)],
) -> TenantContext:
    return TenantContext(
        empresa_id=user.empresa_id,
        user_id=user.user_id,
        roles=user.roles,
        permissions=user.permissions,
    )

