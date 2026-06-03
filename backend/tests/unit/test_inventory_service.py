"""Service-layer tests for the Inventory Management module."""
from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.core.errors import AppError
from app.modules.inventory.schemas import (
    InventoryAggregateMetrics,
    InventoryItemResponse,
    InventoryItemUpdateRequest,
    InventoryListResponse,
    InventoryProductDetailResponse,
    InventoryReservationCreateRequest,
    InventoryReservationResponse,
)
from app.modules.inventory.service import InventoryService


pytestmark = pytest.mark.asyncio


def _tenant() -> SimpleNamespace:
    return SimpleNamespace(empresa_id=uuid4(), user_id=uuid4())


def _summary(status: str = "normal", **kw) -> SimpleNamespace:
    base = dict(
        product_id=uuid4(),
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
    return SimpleNamespace(**base)


def _item(stock_actual: int = 10, stock_minimo: int = 2, stock_reservado: int = 0) -> SimpleMock:
    class _Item(SimpleNamespace):
        @property
        def stock_disponible(self) -> int:
            return max(0, int(self.stock_actual) - int(self.stock_reservado))

    item = _Item()
    item.product_id = uuid4()
    item.stock_actual = stock_actual
    item.stock_minimo = stock_minimo
    item.stock_reservado = stock_reservado
    item.last_movement_at = datetime.now(UTC)
    item.updated_at = datetime.now(UTC)
    return item


class TestListInventory:
    async def test_returns_items_and_passes_filters(self) -> None:
        repo = AsyncMock()
        repo.list_with_product.return_value = (
            [
                (SimpleNamespace(id=uuid4(), name="P1", category="x", base_price="1",
                                 variants=[], images=[], updated_at=datetime.now(UTC)), _summary("normal")),
            ],
            1,
        )
        service = InventoryService(repository=repo)
        result = await service.list_inventory(
            tenant=_tenant(),
            limit=25,
            offset=0,
            search=None,
            category=None,
            status="all",
            sort_by="name",
            sort_dir="asc",
        )
        assert isinstance(result, InventoryListResponse)
        assert result.total == 1
        repo.list_with_product.assert_awaited_once()

    async def test_status_filter_applied_post_fetch(self) -> None:
        repo = AsyncMock()
        repo.list_with_product.return_value = (
            [
                (SimpleNamespace(id=uuid4(), name="Low", category="x", base_price="1",
                                 variants=[], images=[], updated_at=datetime.now(UTC)), _summary("stock_bajo")),
                (SimpleNamespace(id=uuid4(), name="OK", category="x", base_price="1",
                                 variants=[], images=[], updated_at=datetime.now(UTC)), _summary("normal")),
            ],
            2,
        )
        service = InventoryService(repository=repo)
        result = await service.list_inventory(
            tenant=_tenant(),
            limit=25,
            offset=0,
            search=None,
            category=None,
            status="stock_bajo",
            sort_by="name",
            sort_dir="asc",
        )
        assert all(item.status == "stock_bajo" for item in result.items)
        assert result.total == 2  # repo total is the unfiltered count


class TestGetProductDetail:
    async def test_returns_404_when_product_missing(self) -> None:
        repo = AsyncMock()
        repo.get_product_for_inventory.return_value = None
        service = InventoryService(repository=repo)
        with pytest.raises(AppError) as exc:
            await service.get_product_detail(tenant=_tenant(), product_id=uuid4())
        assert exc.value.status_code == 404

    async def test_builds_detail_with_movements_and_reservations(self) -> None:
        product_id = uuid4()
        product = SimpleNamespace(
            id=product_id, name="Polo", category="polos", base_price="29.90",
            variants=[], images=[], updated_at=datetime.now(UTC),
        )
        repo = AsyncMock()
        repo.get_product_for_inventory.return_value = product
        repo.get_item_for_product.return_value = _summary("normal")
        movement = SimpleNamespace(
            id=uuid4(), product_id=product_id, tipo="entrada", cantidad=5,
            motivo="restock", ref_type="manual", ref_id=None,
            created_at=datetime.now(UTC),
        )
        reservation = SimpleNamespace(
            id=uuid4(), product_id=product_id, quantity=2, status="active",
            ref_type="manual", ref_id=None, expires_at=None,
            created_at=datetime.now(UTC), updated_at=datetime.now(UTC),
        )
        repo.list_movements.return_value = ([movement], 1)
        repo.list_reservations.return_value = ([reservation], 1)
        repo.aggregate_metrics.return_value = {
            "total_products": 1,
            "out_of_stock": 0,
            "low_stock": 0,
            "normal_stock": 1,
            "inventory_value": "29.90",
            "total_units": 10,
            "total_reserved_units": 1,
        }
        repo.top_selling.return_value = []
        repo.lowest_stock.return_value = []

        service = InventoryService(repository=repo)
        result = await service.get_product_detail(tenant=_tenant(), product_id=product_id)
        assert isinstance(result, InventoryProductDetailResponse)
        assert result.product.product_id == product_id
        assert len(result.recent_movements) == 1
        assert len(result.active_reservations) == 1


class TestUpdateItem:
    async def test_raises_404_when_product_missing(self) -> None:
        repo = AsyncMock()
        repo.get_product_for_inventory.return_value = None
        service = InventoryService(repository=repo)
        with pytest.raises(AppError):
            await service.update_item(
                tenant=_tenant(),
                product_id=uuid4(),
                payload=InventoryItemUpdateRequest(stock_actual=10),
            )

    async def test_records_movement_only_when_motivo_provided(self) -> None:
        product_id = uuid4()
        repo = AsyncMock()
        repo.get_product_for_inventory.return_value = SimpleNamespace(
            id=product_id, variants=[], images=[],
        )
        item = _item(stock_actual=5, stock_minimo=1)
        repo.upsert_item.return_value = item
        service = InventoryService(repository=repo)

        result = await service.update_item(
            tenant=_tenant(),
            product_id=product_id,
            payload=InventoryItemUpdateRequest(stock_actual=20),
        )
        assert isinstance(result, InventoryItemResponse)
        repo.record_movement.assert_not_awaited()

        # With motivo, movement is recorded as ajuste
        await service.update_item(
            tenant=_tenant(),
            product_id=product_id,
            payload=InventoryItemUpdateRequest(stock_actual=30, motivo="reposición"),
        )
        repo.record_movement.assert_awaited_once()
        call_kwargs = repo.record_movement.await_args.kwargs
        assert call_kwargs["tipo"] == "ajuste"
        assert call_kwargs["motivo"] == "reposición"


class TestCreateReservation:
    async def test_raises_422_when_insufficient_stock(self) -> None:
        repo = AsyncMock()
        item = _item(stock_actual=2, stock_minimo=1, stock_reservado=1)
        repo.get_item_or_404.return_value = item
        service = InventoryService(repository=repo)
        with pytest.raises(AppError) as exc:
            await service.create_reservation(
                tenant=_tenant(),
                payload=InventoryReservationCreateRequest(product_id=item.product_id, quantity=5),
            )
        assert exc.value.status_code == 422

    async def test_increments_reservado_and_records_movement(self) -> None:
        product_id = uuid4()
        repo = AsyncMock()
        item = _item(stock_actual=10, stock_minimo=1, stock_reservado=2)
        item.product_id = product_id
        repo.get_item_or_404.return_value = item
        reservation = SimpleNamespace(
            id=uuid4(), product_id=product_id, quantity=3, status="active",
            ref_type=None, ref_id=None, expires_at=None,
            created_at=datetime.now(UTC), updated_at=datetime.now(UTC),
        )
        repo.create_reservation.return_value = reservation
        service = InventoryService(repository=repo)

        result = await service.create_reservation(
            tenant=_tenant(),
            payload=InventoryReservationCreateRequest(product_id=product_id, quantity=3),
        )
        assert isinstance(result, InventoryReservationResponse)
        assert item.stock_reservado == 5
        repo.record_movement.assert_awaited_once()
        assert repo.record_movement.await_args.kwargs["tipo"] == "reserva"


class TestCancelReservation:
    async def test_raises_404_when_missing(self) -> None:
        repo = AsyncMock()
        repo.get_reservation.return_value = None
        service = InventoryService(repository=repo)
        with pytest.raises(AppError):
            await service.cancel_reservation(tenant=_tenant(), reservation_id=uuid4())

    async def test_raises_409_when_already_cancelled(self) -> None:
        repo = AsyncMock()
        repo.get_reservation.return_value = SimpleNamespace(
            id=uuid4(), product_id=uuid4(), quantity=1, status="cancelled",
        )
        service = InventoryService(repository=repo)
        with pytest.raises(AppError) as exc:
            await service.cancel_reservation(tenant=_tenant(), reservation_id=uuid4())
        assert exc.value.status_code == 409

    async def test_cancels_active_reservation_and_frees_stock(self) -> None:
        product_id = uuid4()
        repo = AsyncMock()
        reservation = SimpleNamespace(
            id=uuid4(), product_id=product_id, quantity=4, status="active",
            ref_type="manual", ref_id=None, expires_at=None,
            created_at=datetime.now(UTC), updated_at=datetime.now(UTC),
        )
        item = _item(stock_actual=10, stock_minimo=1, stock_reservado=6)
        item.product_id = product_id
        repo.get_reservation.return_value = reservation
        repo.get_item_for_product.return_value = item
        service = InventoryService(repository=repo)

        result = await service.cancel_reservation(tenant=_tenant(), reservation_id=reservation.id)
        assert isinstance(result, InventoryReservationResponse)
        assert reservation.status == "cancelled"
        assert item.stock_reservado == 2
        repo.record_movement.assert_awaited_once()
        assert repo.record_movement.await_args.kwargs["tipo"] == "liberacion"


class TestGetMetrics:
    async def test_returns_aggregate_metrics(self) -> None:
        repo = AsyncMock()
        repo.aggregate_metrics.return_value = {
            "total_products": 5,
            "out_of_stock": 1,
            "low_stock": 2,
            "normal_stock": 2,
            "inventory_value": "100.00",
            "total_units": 50,
            "total_reserved_units": 3,
        }
        repo.top_selling.return_value = [
            {"product_id": uuid4(), "name": "Top", "units_sold": 10, "revenue": "300.00"},
        ]
        repo.lowest_stock.return_value = [
            {"product_id": uuid4(), "name": "Low", "stock_actual": 0, "stock_minimo": 1, "status": "agotado"},
        ]
        service = InventoryService(repository=repo)
        result = await service.get_metrics(tenant=_tenant())
        assert isinstance(result, InventoryAggregateMetrics)
        assert result.total_products == 5
        assert len(result.top_selling_products) == 1
        assert result.lowest_stock_products[0].status == "agotado"


# Helper class that behaves like a real SimpleNamespace with attribute writes
class SimpleMock(SimpleNamespace):
    pass
