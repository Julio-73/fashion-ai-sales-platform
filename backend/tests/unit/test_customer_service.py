"""Tests for CustomerService."""
from __future__ import annotations
from unittest.mock import AsyncMock, patch
from uuid import uuid4
from datetime import datetime, timezone
import pytest
from sqlalchemy.exc import IntegrityError
from app.core.errors import AppError
from app.modules.customers.models import Cliente
from app.modules.customers.schemas import CustomerCreateRequest, CustomerUpdateRequest
from tests.conftest import TEST_CUSTOMER_ID

pytestmark = pytest.mark.asyncio
_now = datetime.now(timezone.utc)


def _make_cliente(**kw):
    defaults = dict(id=uuid4(), empresa_id=TEST_CUSTOMER_ID, full_name="Test",
                    email="t@t.com", phone=None, whatsapp=None, instagram_username=None,
                    tags=[], notes=None, lead_status="new", source=None, assigned_to=None,
                    created_at=_now, updated_at=_now, deleted_at=None)
    defaults.update(kw)
    return Cliente(**defaults)


class TestCreateCustomer:
    async def test_creates_customer_successfully(self, customer_service, customer_repository, tenant_context):
        payload = CustomerCreateRequest(full_name="  Maria Garcia Lopez  ", email="maria@example.com",
                                        phone="+51999123456", tags=["vip", "nuevo"], lead_status="new")
        mock_c = _make_cliente(full_name="Maria Garcia Lopez", email="maria@example.com",
                               phone="+51999123456", tags=["vip", "nuevo"], lead_status="new",
                               empresa_id=tenant_context.empresa_id)
        customer_repository.create = AsyncMock(return_value=mock_c)
        customer_repository.commit = AsyncMock()
        result = await customer_service.create_customer(tenant=tenant_context, payload=payload)
        assert result.full_name == "Maria Garcia Lopez"
        assert result.tags == ["vip", "nuevo"]

    async def test_empty_name_raises_422(self, customer_service, tenant_context):
        with pytest.raises(AppError) as e:
            await customer_service.create_customer(tenant=tenant_context,
                                                   payload=CustomerCreateRequest(full_name="  ", email="t@t.com"))
        assert e.value.status_code == 422
        assert e.value.code == "invalid_input"

    async def test_duplicate_email_raises_409(self, customer_service, customer_repository, tenant_context):
        customer_repository.create = AsyncMock(side_effect=IntegrityError("mock", None, None))
        customer_repository.rollback = AsyncMock()
        with pytest.raises(AppError) as e:
            await customer_service.create_customer(tenant=tenant_context,
                                                   payload=CustomerCreateRequest(full_name="T", email="d@d.com"))
        assert e.value.status_code == 409

    async def test_tags_are_sanitized(self, customer_service, customer_repository, tenant_context):
        # Tags with whitespace and duplicates should be sanitized (but schema validates max 48)
        payload = CustomerCreateRequest(full_name="User", email="u@u.com", tags=["  VIP  ", "vip"])
        mock_c = _make_cliente(tags=["VIP", "vip"], empresa_id=tenant_context.empresa_id)
        customer_repository.create = AsyncMock(return_value=mock_c)
        customer_repository.commit = AsyncMock()
        await customer_service.create_customer(tenant=tenant_context, payload=payload)
        sent = customer_repository.create.call_args.kwargs["payload"]
        assert "VIP" in sent.tags
        assert len(sent.tags) == 2  # Both tags preserved (strip happens but not dedup in payload)

    async def test_schema_rejects_overlong_tags(self):
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            CustomerCreateRequest(full_name="T", email="t@t.com", tags=["a" * 49])


class TestGetCustomer:
    async def test_returns_customer(self, customer_service, customer_repository, tenant_context):
        mock_c = _make_cliente(id=TEST_CUSTOMER_ID, empresa_id=tenant_context.empresa_id)
        customer_repository.get_by_id = AsyncMock(return_value=mock_c)
        result = await customer_service.get_customer(tenant=tenant_context, customer_id=TEST_CUSTOMER_ID)
        assert result.id == TEST_CUSTOMER_ID

    async def test_not_found_raises_404(self, customer_service, customer_repository, tenant_context):
        customer_repository.get_by_id = AsyncMock(return_value=None)
        with pytest.raises(AppError) as e:
            await customer_service.get_customer(tenant=tenant_context, customer_id=uuid4())
        assert e.value.status_code == 404


class TestListCustomers:
    async def test_returns_paginated_list(self, customer_service, customer_repository, tenant_context):
        mock_c = _make_cliente(empresa_id=tenant_context.empresa_id)
        customer_repository.list = AsyncMock(return_value=([mock_c], 1))
        result = await customer_service.list_customers(tenant=tenant_context, limit=25, offset=0, search=None, lead_status=None)
        assert len(result.items) == 1
        assert result.total == 1


class TestUpdateCustomer:
    async def test_updates_customer(self, customer_service, customer_repository, tenant_context):
        mock_c = _make_cliente(id=TEST_CUSTOMER_ID, full_name="Old", empresa_id=tenant_context.empresa_id)
        customer_repository.get_by_id = AsyncMock(return_value=mock_c)
        customer_repository.update = AsyncMock(return_value=mock_c)
        customer_repository.commit = AsyncMock()
        await customer_service.update_customer(tenant=tenant_context, customer_id=TEST_CUSTOMER_ID,
                                               payload=CustomerUpdateRequest(full_name="  New  "))
        assert customer_repository.update.call_args.kwargs["payload"]["full_name"] == "New"

    async def test_not_found_raises_404(self, customer_service, customer_repository, tenant_context):
        customer_repository.get_by_id = AsyncMock(return_value=None)
        with pytest.raises(AppError) as e:
            await customer_service.update_customer(tenant=tenant_context, customer_id=uuid4(),
                                                   payload=CustomerUpdateRequest(full_name="New"))
        assert e.value.status_code == 404


class TestDeleteCustomer:
    async def test_soft_deletes_customer(self, customer_service, customer_repository, tenant_context):
        mock_c = _make_cliente(empresa_id=tenant_context.empresa_id)
        customer_repository.get_by_id = AsyncMock(return_value=mock_c)
        customer_repository.soft_delete = AsyncMock()
        customer_repository.commit = AsyncMock()
        await customer_service.delete_customer(tenant=tenant_context, customer_id=TEST_CUSTOMER_ID)
        customer_repository.soft_delete.assert_awaited_once()

    async def test_not_found_raises_404(self, customer_service, customer_repository, tenant_context):
        customer_repository.get_by_id = AsyncMock(return_value=None)
        with pytest.raises(AppError) as e:
            await customer_service.delete_customer(tenant=tenant_context, customer_id=uuid4())
        assert e.value.status_code == 404
