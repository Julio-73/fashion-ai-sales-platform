"""API tests for the CRM Customer 360 endpoints.

These tests use FastAPI's dependency overrides to inject a mock
``CrmService`` and a mock ``TenantContext``, so no database is required.
"""
from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.security.dependencies import TenantContext, get_tenant_context
from app.main import app
from app.modules.crm.dependencies import get_crm_service
from app.modules.crm.schemas import (
    Customer360Summary,
    CustomerAggregateMetrics,
    CustomerMetrics,
    CustomerOrderHistoryItem,
    CustomerOrderHistoryResponse,
)
from app.modules.crm.service import CrmService


pytestmark = pytest.mark.asyncio


EMPRESA_ID = UUID("11111111-1111-4111-8111-111111111111")
USER_ID = UUID("22222222-2222-4222-8222-222222222222")


def _tenant() -> TenantContext:
    return TenantContext(
        empresa_id=EMPRESA_ID,
        user_id=USER_ID,
        roles=["owner"],
        permissions={
            "customers:read",
            "customers:write",
            "orders:read",
            "orders:write",
        },
    )


def _summary(status: str = "nuevo", **overrides) -> Customer360Summary:
    metrics = CustomerMetrics(
        order_count=0,
        lifetime_value=Decimal("0"),
        average_ticket=Decimal("0"),
        first_purchase_at=None,
        last_purchase_at=None,
        days_since_last_purchase=None,
        status=status,
    )
    if status == "vip":
        metrics = CustomerMetrics(
            order_count=7,
            lifetime_value=Decimal("2500"),
            average_ticket=Decimal("357.14"),
            first_purchase_at=datetime(2025, 6, 1, tzinfo=UTC),
            last_purchase_at=datetime(2026, 5, 30, tzinfo=UTC),
            days_since_last_purchase=3,
            status="vip",
        )
    base = {
        "id": uuid4(),
        "empresa_id": EMPRESA_ID,
        "full_name": "Carolina Test",
        "email": "carolina@test.com",
        "phone": "+51 999 000 001",
        "whatsapp": "+51 999 000 001",
        "instagram_username": None,
        "tags": ["vip"],
        "notes": None,
        "lead_status": "won",
        "source": "demo",
        "assigned_to": None,
        "created_at": datetime(2025, 1, 1, tzinfo=UTC),
        "updated_at": datetime(2026, 5, 30, tzinfo=UTC),
        "metrics": metrics,
    }
    base.update(overrides)
    return Customer360Summary(**base)


def _make_client(mock_service: CrmService) -> TestClient:
    app.dependency_overrides[get_crm_service] = lambda: mock_service
    app.dependency_overrides[get_tenant_context] = lambda: _tenant()
    return TestClient(app)


@pytest.fixture(autouse=True)
def _clear_overrides():
    yield
    app.dependency_overrides.clear()


class TestCrmMetrics:
    async def test_metrics_endpoint(self):
        service = AsyncMock(spec=CrmService)
        service.get_metrics = AsyncMock(
            return_value=CustomerAggregateMetrics(
                total_customers=18,
                new_customers=9,
                active_customers=3,
                recurrent_customers=3,
                vip_customers=3,
                inactive_customers=0,
                total_lifetime_value=Decimal("9688.97"),
                average_ticket=Decimal("284.96"),
                average_orders_per_customer=Decimal("1.88"),
            )
        )
        with _make_client(service) as client:
            response = client.get("/api/v1/crm/metrics")
        assert response.status_code == 200
        body = response.json()
        assert body["total_customers"] == 18
        assert body["vip_customers"] == 3


class TestCrmCustomerList:
    async def test_list_returns_items_and_aggregate(self):
        service = AsyncMock(spec=CrmService)
        service.list_customer_360 = AsyncMock(
            return_value={
                "items": [_summary("vip"), _summary("nuevo")],
                "total": 2,
                "limit": 25,
                "offset": 0,
                "aggregate": CustomerAggregateMetrics(
                    total_customers=2, vip_customers=1, new_customers=1
                ),
            }
        )
        with _make_client(service) as client:
            response = client.get("/api/v1/crm/customers?limit=25")
        assert response.status_code == 200
        body = response.json()
        assert body["total"] == 2
        assert len(body["items"]) == 2
        assert body["aggregate"]["vip_customers"] == 1


class TestCrmCustomerDetail:
    async def test_get_returns_summary(self):
        cust_id = uuid4()
        service = AsyncMock(spec=CrmService)
        service.get_customer_360 = AsyncMock(return_value=_summary("vip", id=cust_id))
        with _make_client(service) as client:
            response = client.get(f"/api/v1/crm/customers/{cust_id}")
        assert response.status_code == 200
        body = response.json()
        assert body["id"] == str(cust_id)
        assert body["metrics"]["status"] == "vip"
        assert body["metrics"]["order_count"] == 7


class TestCrmCustomerOrders:
    async def test_orders_endpoint_returns_history(self):
        cust_id = uuid4()
        service = AsyncMock(spec=CrmService)
        service.list_customer_orders = AsyncMock(
            return_value=CustomerOrderHistoryResponse(
                customer_id=cust_id,
                total=2,
                limit=10,
                offset=0,
                items=[
                    CustomerOrderHistoryItem(
                        order_id=uuid4(),
                        order_number="ORD-000001",
                        created_at=datetime(2026, 5, 1, tzinfo=UTC),
                        status="delivered",
                        total=Decimal("450.00"),
                        items_count=2,
                        primary_product_name="Vestido floral",
                    )
                ],
            )
        )
        with _make_client(service) as client:
            response = client.get(f"/api/v1/crm/customers/{cust_id}/orders")
        assert response.status_code == 200
        body = response.json()
        assert body["total"] == 2
        assert body["items"][0]["order_number"] == "ORD-000001"
