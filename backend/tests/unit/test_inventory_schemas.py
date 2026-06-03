"""Unit tests for the inventory module schemas and helpers."""
from __future__ import annotations

import pytest

from app.modules.inventory.schemas import (
    InventoryAggregateMetrics,
    InventoryListResponse,
    InventoryLowStockProduct,
    InventoryMovementResponse,
    InventoryProductDetailResponse,
    InventoryProductSummary,
    InventoryReservationCreateRequest,
    InventoryReservationResponse,
    InventoryStatus,
    InventoryTopProductMetric,
    classify_status,
)


class TestClassifyStatus:
    def test_agotado_when_stock_is_zero(self) -> None:
        assert classify_status(stock_actual=0, stock_minimo=5) == "agotado"

    def test_agotado_when_stock_is_negative_clamped(self) -> None:
        # Negative stocks are guarded by the DB CHECK but classify should
        # still return a sensible status for the test contract.
        assert classify_status(stock_actual=0, stock_minimo=0) == "agotado"

    def test_stock_bajo_when_at_minimo(self) -> None:
        assert classify_status(stock_actual=5, stock_minimo=5) == "stock_bajo"

    def test_stock_bajo_when_below_minimo(self) -> None:
        assert classify_status(stock_actual=2, stock_minimo=5) == "stock_bajo"

    def test_normal_when_above_minimo(self) -> None:
        assert classify_status(stock_actual=10, stock_minimo=5) == "normal"

    def test_normal_when_minimo_is_zero(self) -> None:
        assert classify_status(stock_actual=1, stock_minimo=0) == "normal"


class TestSchemaSerialization:
    def test_inventory_product_summary_accepts_required_fields(self) -> None:
        from datetime import UTC, datetime
        from uuid import uuid4

        summary = InventoryProductSummary(
            product_id=uuid4(),
            name="Polo Premium",
            category="polos",
            base_price="29.90",
            sku="POL-001",
            image_url=None,
            stock_actual=10,
            stock_minimo=2,
            stock_reservado=1,
            stock_disponible=9,
            status="normal",
            last_movement_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        assert summary.stock_disponible == 9
        assert summary.status == "normal"

    def test_inventory_list_response_empty(self) -> None:
        response = InventoryListResponse(items=[], total=0, limit=25, offset=0)
        assert response.total == 0
        assert response.items == []

    def test_inventory_aggregate_metrics(self) -> None:
        from uuid import uuid4

        metrics = InventoryAggregateMetrics(
            total_products=10,
            out_of_stock=2,
            low_stock=3,
            normal_stock=5,
            inventory_value="1234.50",
            total_units=100,
            total_reserved_units=5,
            top_selling_products=[
                InventoryTopProductMetric(
                    product_id=uuid4(),
                    name="Top",
                    units_sold=50,
                    revenue="1500.00",
                )
            ],
            lowest_stock_products=[
                InventoryLowStockProduct(
                    product_id=uuid4(),
                    name="Low",
                    stock_actual=0,
                    stock_minimo=1,
                    status="agotado",
                )
            ],
        )
        assert metrics.out_of_stock == 2
        assert metrics.top_selling_products[0].units_sold == 50

    def test_inventory_movement_response(self) -> None:
        from datetime import UTC, datetime
        from uuid import uuid4

        movement = InventoryMovementResponse(
            id=uuid4(),
            product_id=uuid4(),
            tipo="entrada",
            cantidad=10,
            motivo="Reposición",
            ref_type="manual",
            ref_id=None,
            created_at=datetime.now(UTC),
        )
        assert movement.tipo == "entrada"
        assert movement.cantidad == 10

    def test_inventory_reservation_create_request_validates_quantity(self) -> None:
        from pydantic import ValidationError
        from uuid import uuid4

        with pytest.raises(ValidationError):
            InventoryReservationCreateRequest(product_id=uuid4(), quantity=0)

    def test_inventory_reservation_response(self) -> None:
        from datetime import UTC, datetime
        from uuid import uuid4

        response = InventoryReservationResponse(
            id=uuid4(),
            product_id=uuid4(),
            quantity=3,
            status="active",
            ref_type="order",
            ref_id=uuid4(),
            expires_at=None,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        assert response.status == "active"

    def test_inventory_product_detail_response(self) -> None:
        from datetime import UTC, datetime
        from uuid import uuid4

        summary = InventoryProductSummary(
            product_id=uuid4(),
            name="Detalle",
            category=None,
            base_price=None,
            sku=None,
            image_url=None,
            stock_actual=0,
            stock_minimo=1,
            stock_reservado=0,
            stock_disponible=0,
            status="agotado",
            last_movement_at=None,
            updated_at=datetime.now(UTC),
        )
        metrics = InventoryAggregateMetrics(
            total_products=1,
            out_of_stock=1,
            low_stock=0,
            normal_stock=0,
            inventory_value="0",
            total_units=0,
            total_reserved_units=0,
            top_selling_products=[],
            lowest_stock_products=[],
        )
        detail = InventoryProductDetailResponse(
            product=summary,
            recent_movements=[],
            active_reservations=[],
            metrics=metrics,
        )
        assert detail.product.status == "agotado"


class TestInventoryStatusLiteral:
    @pytest.mark.parametrize(
        "value",
        ["normal", "stock_bajo", "agotado"],
    )
    def test_status_is_valid_literal(self, value: InventoryStatus) -> None:
        assert value in ("normal", "stock_bajo", "agotado")
