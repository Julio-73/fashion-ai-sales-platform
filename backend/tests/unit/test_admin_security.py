"""Unit tests for the Admin module security layer.

Covers:
- ``create_admin_access_token`` / ``verify_admin_access_token`` round-trip.
- ``AdminContext`` has_permission and is_super_admin flags.
- ``require_admin_permission`` dependency rejects missing permissions.
- The admin token uses its own ``typ`` and ``aud`` (does not collide
  with the frozen ``TokenPayload``).
"""
from __future__ import annotations

from typing import Annotated
from uuid import UUID, uuid4

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.core.errors import AppError, register_exception_handlers
from app.modules.admin.security import (
    ADMIN_TOKEN_AUDIENCE,
    ADMIN_TOKEN_ISSUER,
    ADMIN_TOKEN_TYPE,
    AdminContext,
    SUPER_ADMIN_ROLE,
    bearer_scheme,
    create_admin_access_token,
    get_admin_context,
    require_admin_permission,
    require_super_admin,
    verify_admin_access_token,
)


def _new_app() -> FastAPI:
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/me")
    def me(ctx: Annotated[AdminContext, Depends(get_admin_context)]):
        return {
            "user_id": str(ctx.user_id),
            "email": ctx.email,
            "is_super_admin": ctx.is_super_admin,
        }

    @app.get("/tenants")
    def list_t(
        ctx: Annotated[AdminContext, Depends(require_admin_permission("admin:tenants:read"))],
    ):
        return {"ok": True, "user": ctx.email}

    @app.get("/super-only")
    def super_only(
        ctx: Annotated[AdminContext, Depends(require_super_admin())],
    ):
        return {"ok": True, "user": ctx.email}

    return app


def test_admin_token_round_trip() -> None:
    user_id = uuid4()
    token = create_admin_access_token(
        user_id=user_id, email="ops@test.io", roles=[SUPER_ADMIN_ROLE]
    )
    payload = verify_admin_access_token(token)
    assert payload.sub == user_id
    assert payload.email == "ops@test.io"
    assert payload.roles == [SUPER_ADMIN_ROLE]
    assert payload.typ == ADMIN_TOKEN_TYPE
    assert payload.iss == ADMIN_TOKEN_ISSUER
    assert payload.aud == ADMIN_TOKEN_AUDIENCE


def test_admin_token_rejects_other_typ() -> None:
    """A token emitted by the tenant auth flow (``typ='access'``) must be rejected."""
    import time

    from jose import jwt

    from app.core.config import get_settings

    settings = get_settings()
    now = int(time.time())
    payload = {
        "sub": str(uuid4()),
        "email": "x@y.io",
        "roles": ["super_admin"],
        "permissions": [],
        "jti": "x",
        "typ": "access",
        "iss": ADMIN_TOKEN_ISSUER,
        "aud": ADMIN_TOKEN_AUDIENCE,
        "iat": now,
        "exp": now + 60,
    }
    admin_key = settings.admin_jwt_secret_key or settings.jwt_secret_key
    token = jwt.encode(payload, admin_key, algorithm=settings.jwt_algorithm)
    with pytest.raises(AppError) as exc:
        verify_admin_access_token(token)
    assert exc.value.status_code == 401
    assert exc.value.code == "invalid_token_type"


def test_admin_token_rejects_tampered_signature() -> None:
    user_id = uuid4()
    token = create_admin_access_token(
        user_id=user_id, email="ops@test.io", roles=[SUPER_ADMIN_ROLE]
    )
    # Flip the last char of the signature
    tampered = token[:-1] + ("a" if token[-1] != "a" else "b")
    with pytest.raises(AppError) as exc:
        verify_admin_access_token(tampered)
    assert exc.value.status_code == 401


def test_admin_context_has_permission_and_super_admin() -> None:
    ctx = AdminContext(
        user_id=UUID(int=1),
        email="x",
        roles=[SUPER_ADMIN_ROLE],
        permissions={"admin:tenants:read", "admin:audit:read"},
        is_super_admin=True,
    )
    assert ctx.has_permission("admin:tenants:read")
    assert not ctx.has_permission("admin:nope")
    assert ctx.is_super_admin is True


def test_get_admin_context_requires_token() -> None:
    app = _new_app()
    client = TestClient(app)
    r = client.get("/me")
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "not_authenticated"


def test_get_admin_context_returns_context() -> None:
    user_id = uuid4()
    token = create_admin_access_token(
        user_id=user_id, email="ops@test.io", roles=[SUPER_ADMIN_ROLE]
    )
    app = _new_app()
    client = TestClient(app, headers={"Authorization": f"Bearer {token}"})
    r = client.get("/me")
    assert r.status_code == 200
    body = r.json()
    assert body["user_id"] == str(user_id)
    assert body["email"] == "ops@test.io"
    assert body["is_super_admin"] is True


def test_require_admin_permission_403() -> None:
    user_id = uuid4()
    token = create_admin_access_token(
        user_id=user_id, email="agent@test.io", roles=["agent"]
    )
    app = _new_app()
    client = TestClient(app, headers={"Authorization": f"Bearer {token}"})
    r = client.get("/tenants")
    assert r.status_code == 403
    assert r.json()["error"]["code"] == "permission_denied"


def test_require_admin_permission_passes() -> None:
    user_id = uuid4()
    token = create_admin_access_token(
        user_id=user_id, email="ops@test.io", roles=[SUPER_ADMIN_ROLE]
    )
    app = _new_app()
    client = TestClient(app, headers={"Authorization": f"Bearer {token}"})
    r = client.get("/tenants")
    assert r.status_code == 200


def test_require_super_admin_blocks_company_admin() -> None:
    user_id = uuid4()
    token = create_admin_access_token(
        user_id=user_id, email="ca@test.io", roles=["company_admin"]
    )
    app = _new_app()
    client = TestClient(app, headers={"Authorization": f"Bearer {token}"})
    r = client.get("/super-only")
    assert r.status_code == 403
    assert r.json()["error"]["code"] == "super_admin_required"


def test_require_super_admin_allows_super_admin() -> None:
    user_id = uuid4()
    token = create_admin_access_token(
        user_id=user_id, email="sa@test.io", roles=[SUPER_ADMIN_ROLE]
    )
    app = _new_app()
    client = TestClient(app, headers={"Authorization": f"Bearer {token}"})
    r = client.get("/super-only")
    assert r.status_code == 200


def test_bearer_scheme_auto_error_disabled() -> None:
    """``HTTPBearer(auto_error=False)`` is the configured instance; it must
    not raise on missing credentials (so the dependency can return a
    401 with the project's standard error envelope)."""
    from fastapi.security import HTTPBearer

    assert isinstance(bearer_scheme, HTTPBearer)
    assert bearer_scheme.auto_error is False

