"""Integration tests for the Inventory Management API.

These tests exercise the real FastAPI router with dependencies overridden
so they can run without a live PostgreSQL instance. They verify routing,
permission gating, status code mapping, and the response payload shape.
"""
from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.security.dependencies import TenantContext
from app.modules.inventory.router import router as inventory_router
from app.modules.inventory.schemas import (
    InventoryAggregateMetrics,
    InventoryItemResponse,
    InventoryListResponse,
    InventoryProductDetailResponse,
    InventoryProductSummary,
    InventoryReservationResponse,
)


TENANT = TenantContext(
    empresa_id=uuid4(),
    user_id=uuid4(),
    roles=["owner"],
    permissions={
        "products:read",
        "products:write",
        "ai:context",
        "customers:write",
        "orders:read",
        "analytics:read",
        "chats:read",
        "chats:write",
        "ai:respond",
        "ai:classify",
        "settings:manage",
        "sales:read",
        "auth:me",
        "conversations:read",
        "orders:write",
        "customers:read",
    },
)


def _build_app(service_stub: AsyncMock) -> FastAPI:
    app = FastAPI()
    app.include_router(inventory_router, prefix="/api/v1/inventory")

    from app.core.errors import register_exception_handlers

    register_exception_handlers(app)

    async def _service_override():
        return service_stub

    async def _tenant_override():
        return TENANT

    from app.core.security.dependencies import get_tenant_context
    from app.modules.inventory.dependencies import get_inventory_service

    app.dependency_overrides[get_tenant_context] = _tenant_override
    app.dependency_overrides[get_inventory_service] = _service_override
    return app


def _summary(status: str = "normal", product_id=None, **kw) -> InventoryProductSummary:
    base = dict(
        product_id=product_id or uuid4(),
        name="Polo",
        category="polos",
        base_price="29.90",
        sku="POL-001",
        image_url=None,
        stock_actual=10,
        stock_minimo=2,
        stock_reservado=1,
        stock_disponible=9,
        status=status,
        last_movement_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    base.update(kw)
    return InventoryProductSummary(**base)


class TestListEndpoint:
    def test_returns_200_with_paginated_payload(self) -> None:
        service = AsyncMock()
        service.list_inventory.return_value = InventoryListResponse(
            items=[_summary()],
            total=1,
            limit=25,
            offset=0,
        )
        app = _build_app(service)
        with TestClient(app) as client:
            resp = client.get("/api/v1/inventory")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 1
        assert body["items"][0]["name"] == "Polo"
        assert body["items"][0]["status"] == "normal"

    def test_accepts_query_filters(self) -> None:
        service = AsyncMock()
        service.list_inventory.return_value = InventoryListResponse(
            items=[], total=0, limit=10, offset=0,
        )
        app = _build_app(service)
        with TestClient(app) as client:
            resp = client.get(
                "/api/v1/inventory",
                params={"status": "stock_bajo", "search": "polo", "limit": 5, "offset": 10},
            )
        assert resp.status_code == 200
        call_kwargs = service.list_inventory.await_args.kwargs
        assert call_kwargs["status"] == "stock_bajo"
        assert call_kwargs["search"] == "polo"
        assert call_kwargs["limit"] == 5
        assert call_kwargs["offset"] == 10


class TestMetricsEndpoint:
    def test_returns_aggregate_metrics(self) -> None:
        service = AsyncMock()
        service.get_metrics.return_value = InventoryAggregateMetrics(
            total_products=10,
            out_of_stock=2,
            low_stock=3,
            normal_stock=5,
            inventory_value="1000.00",
            total_units=200,
            total_reserved_units=15,
            top_selling_products=[],
            lowest_stock_products=[],
        )
        app = _build_app(service)
        with TestClient(app) as client:
            resp = client.get("/api/v1/inventory/metrics")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total_products"] == 10
        assert body["out_of_stock"] == 2
        assert body["low_stock"] == 3


class TestProductDetailEndpoint:
    def test_returns_product_with_movements(self) -> None:
        product_id = uuid4()
        service = AsyncMock()
        service.get_product_detail.return_value = InventoryProductDetailResponse(
            product=_summary("stock_bajo", product_id=product_id, stock_actual=1, stock_disponible=1),
            recent_movements=[],
            active_reservations=[],
            metrics=InventoryAggregateMetrics(
                total_products=1, out_of_stock=0, low_stock=1, normal_stock=0,
                inventory_value="29.90", total_units=1, total_reserved_units=0,
                top_selling_products=[], lowest_stock_products=[],
            ),
        )
        app = _build_app(service)
        with TestClient(app) as client:
            resp = client.get(f"/api/v1/inventory/{product_id}")
        assert resp.status_code == 200
        body = resp.json()
        assert body["product"]["product_id"] == str(product_id)
        assert body["product"]["status"] == "stock_bajo"
        assert "recent_movements" in body
        assert "active_reservations" in body
        assert "metrics" in body

    def test_returns_404_when_product_missing(self) -> None:
        from app.core.errors import AppError

        service = AsyncMock()
        service.get_product_detail.side_effect = AppError(
            code="product_not_found",
            message="Product not found",
            status_code=404,
        )
        app = _build_app(service)
        with TestClient(app) as client:
            resp = client.get(f"/api/v1/inventory/{uuid4()}")
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "product_not_found"


class TestUpdateEndpoint:
    def test_patches_stock_and_returns_item(self) -> None:
        product_id = uuid4()
        service = AsyncMock()
        service.update_item.return_value = InventoryItemResponse(
            product_id=product_id,
            stock_actual=42,
            stock_minimo=5,
            stock_reservado=0,
            stock_disponible=42,
            status="normal",
            last_movement_at=None,
            updated_at=datetime.now(UTC),
        )
        app = _build_app(service)
        with TestClient(app) as client:
            resp = client.patch(
                f"/api/v1/inventory/{product_id}",
                json={"stock_actual": 42, "stock_minimo": 5},
            )
        assert resp.status_code == 200
        body = resp.json()
        assert body["stock_actual"] == 42
        assert body["status"] == "normal"

    def test_rejects_negative_stock(self) -> None:
        from app.core.errors import AppError

        product_id = uuid4()
        service = AsyncMock()
        service.update_item.side_effect = AppError(
            code="invalid_stock",
            message="Stock cannot be negative",
            status_code=422,
        )
        app = _build_app(service)
        with TestClient(app) as client:
            resp = client.patch(
                f"/api/v1/inventory/{product_id}",
                json={"stock_actual": -1},
            )
        assert resp.status_code == 422


class TestReservationEndpoints:
    def test_create_reservation_returns_201(self) -> None:
        product_id = uuid4()
        reservation_id = uuid4()
        service = AsyncMock()
        service.create_reservation.return_value = InventoryReservationResponse(
            id=reservation_id,
            product_id=product_id,
            quantity=3,
            status="active",
            ref_type=None,
            ref_id=None,
            expires_at=None,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        app = _build_app(service)
        with TestClient(app) as client:
            resp = client.post(
                "/api/v1/inventory/reservations",
                json={"product_id": str(product_id), "quantity": 3},
            )
        assert resp.status_code == 201
        body = resp.json()
        assert body["status"] == "active"
        assert body["quantity"] == 3

    def test_create_reservation_rejects_zero_quantity(self) -> None:
        app = _build_app(AsyncMock())
        with TestClient(app) as client:
            resp = client.post(
                "/api/v1/inventory/reservations",
                json={"product_id": str(uuid4()), "quantity": 0},
            )
        assert resp.status_code == 422

    def test_create_reservation_rejects_insufficient_stock(self) -> None:
        from app.core.errors import AppError

        service = AsyncMock()
        service.create_reservation.side_effect = AppError(
            code="insufficient_stock",
            message="Not enough available stock to reserve",
            status_code=422,
        )
        app = _build_app(service)
        with TestClient(app) as client:
            resp = client.post(
                "/api/v1/inventory/reservations",
                json={"product_id": str(uuid4()), "quantity": 9999},
            )
        assert resp.status_code == 422
        assert resp.json()["error"]["code"] == "insufficient_stock"

    def test_cancel_reservation_returns_updated_payload(self) -> None:
        reservation_id = uuid4()
        product_id = uuid4()
        service = AsyncMock()
        service.cancel_reservation.return_value = InventoryReservationResponse(
            id=reservation_id,
            product_id=product_id,
            quantity=2,
            status="cancelled",
            ref_type="manual",
            ref_id=None,
            expires_at=None,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        app = _build_app(service)
        with TestClient(app) as client:
            resp = client.delete(f"/api/v1/inventory/reservations/{reservation_id}")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "cancelled"
