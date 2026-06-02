"""Service-layer tests for CRM Customer 360 business rules."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.modules.crm.schemas import (
    CustomerAggregateMetrics,
    CustomerLifecycleStatus,
)
from app.modules.crm.service import CrmService


pytestmark = pytest.mark.asyncio


def _make_cliente(**kw):
    defaults = dict(
        id=uuid4(),
        empresa_id=uuid4(),
        full_name="Test",
        email="t@t.com",
        phone=None,
        whatsapp=None,
        instagram_username=None,
        tags=[],
        notes=None,
        lead_status="new",
        source=None,
        assigned_to=None,
        created_at=datetime.now(UTC) - timedelta(days=5),
        updated_at=datetime.now(UTC),
    )
    defaults.update(kw)
    return SimpleNamespace(**defaults)


class TestGetMetrics:
    async def test_returns_aggregate_metrics(self):
        repo = AsyncMock()
        repo.aggregate_for_company.return_value = {
            "total_customers": 10,
            "total_lifetime_value": Decimal("5000"),
            "average_ticket": Decimal("250"),
            "average_orders_per_customer": Decimal("2"),
            "vip_count": 2,
            "recurrent_count": 3,
            "inactive_count": 1,
            "new_count": 4,
            "active_count": 2,
        }
        service = CrmService(repository=repo)
        tenant = SimpleNamespace(empresa_id=uuid4())
        result = await service.get_metrics(tenant=tenant)
        assert isinstance(result, CustomerAggregateMetrics)
        assert result.total_customers == 10
        assert result.vip_customers == 2
        assert result.total_lifetime_value == Decimal("5000")


class TestGetCustomer360:
    async def test_raises_404_when_not_found(self):
        repo = AsyncMock()
        repo.get_customer_360.return_value = None
        service = CrmService(repository=repo)
        tenant = SimpleNamespace(empresa_id=uuid4())
        from app.core.errors import AppError

        with pytest.raises(AppError) as exc:
            await service.get_customer_360(tenant=tenant, customer_id=uuid4())
        assert exc.value.status_code == 404
        assert exc.value.code == "customer_not_found"

    async def test_builds_summary_with_vip_status(self):
        cliente = _make_cliente(full_name="VIP Customer")
        repo = AsyncMock()
        repo.get_customer_360.return_value = (
            cliente,
            7,
            Decimal("2500"),
            datetime.now(UTC) - timedelta(days=180),
            datetime.now(UTC) - timedelta(days=2),
        )
        service = CrmService(repository=repo)
        tenant = SimpleNamespace(empresa_id=cliente.empresa_id)
        result = await service.get_customer_360(tenant=tenant, customer_id=cliente.id)
        assert result.full_name == "VIP Customer"
        assert result.metrics.status == CustomerLifecycleStatus.VIP
        assert result.metrics.order_count == 7
        assert result.metrics.lifetime_value == Decimal("2500")


class TestListCustomerOrders:
    async def test_returns_empty_when_customer_not_found(self):
        repo = AsyncMock()
        repo.list_customer_orders.return_value = ([], 0)
        service = CrmService(repository=repo)
        tenant = SimpleNamespace(empresa_id=uuid4())
        result = await service.list_customer_orders(
            tenant=tenant, customer_id=uuid4(), limit=10, offset=0
        )
        assert result.total == 0
        assert result.items == []
