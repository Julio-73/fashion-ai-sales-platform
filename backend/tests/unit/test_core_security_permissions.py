"""Tests for RBAC permissions."""
from __future__ import annotations
from unittest.mock import AsyncMock
import pytest
from app.core.errors import AppError
from app.core.security.permissions import ROLE_PERMISSIONS, permissions_for_roles, require_permission


class TestPermissionsForRoles:
    def test_owner_has_all_permissions(self):
        assert permissions_for_roles(["owner"]) == sorted(ROLE_PERMISSIONS["owner"])

    def test_admin_permissions_subset_of_owner(self):
        admin = set(permissions_for_roles(["admin"]))
        owner = set(permissions_for_roles(["owner"]))
        assert admin.issubset(owner)
        assert "users:manage" not in admin

    def test_sales_agent_has_basic_permissions(self):
        p = set(permissions_for_roles(["sales_agent"]))
        assert "customers:read" in p
        assert "customers:write" in p
        assert "analytics:read" not in p

    def test_analyst_has_read_only(self):
        p = set(permissions_for_roles(["analyst"]))
        assert "customers:read" in p
        assert "customers:write" not in p

    def test_multiple_roles_merged(self):
        p = set(permissions_for_roles(["sales_agent", "analyst"]))
        assert "analytics:read" in p
        assert "customers:write" in p

    def test_unknown_role_returns_empty(self):
        assert permissions_for_roles(["unknown"]) == []


class TestRequirePermission:
    @pytest.mark.asyncio
    async def test_allows_with_correct_permission(self):
        dep = require_permission("customers:read")
        tenant = AsyncMock(permissions={"customers:read", "customers:write"})
        result = await dep(tenant=tenant)
        assert result is tenant

    @pytest.mark.asyncio
    async def test_denies_without_permission(self):
        dep = require_permission("settings:manage")
        tenant = AsyncMock(permissions={"customers:read"})
        with pytest.raises(AppError) as e:
            await dep(tenant=tenant)
        assert e.value.status_code == 403
        assert e.value.code == "permission_denied"
