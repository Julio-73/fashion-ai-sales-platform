"""Business logic for the Inventory Management module."""
from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from app.core.errors import AppError
from app.core.security.dependencies import TenantContext
from app.modules.inventory.models import MovementType
from app.modules.inventory.repository import InventoryRepository
from app.modules.inventory.schemas import (
    InventoryAggregateMetrics,
    InventoryItemResponse,
    InventoryItemUpdateRequest,
    InventoryListResponse,
    InventoryLowStockProduct,
    InventoryMovementResponse,
    InventoryProductDetailResponse,
    InventoryProductSummary,
    InventoryReservationCreateRequest,
    InventoryReservationResponse,
    InventorySortBy,
    InventoryStatusFilter,
    InventoryTopProductMetric,
    classify_status,
)
from app.modules.products.models import Producto


logger = logging.getLogger("ai_sales_agent.inventory")


class InventoryService:
    def __init__(self, repository: InventoryRepository) -> None:
        self._repository = repository

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def list_inventory(
        self,
        *,
        tenant: TenantContext,
        limit: int,
        offset: int,
        search: str | None,
        category: str | None,
        status: InventoryStatusFilter,
        sort_by: InventorySortBy,
        sort_dir: str,
    ) -> InventoryListResponse:
        rows, total = await self._repository.list_with_product(
            empresa_id=tenant.empresa_id,
            limit=limit,
            offset=offset,
            search=search,
            category=category,
            status=status,
            sort_by=sort_by,
            sort_dir=sort_dir,
        )
        items = [self._build_summary(product=product, item=item) for product, item in rows]
        if status != "all":
            items = [s for s in items if s.status == status]
        return InventoryListResponse(
            items=items, total=total, limit=limit, offset=offset
        )

    async def get_product_detail(
        self, *, tenant: TenantContext, product_id: UUID
    ) -> InventoryProductDetailResponse:
        product = await self._repository.get_product_for_inventory(
            empresa_id=tenant.empresa_id, product_id=product_id
        )
        if product is None:
            raise AppError(
                code="product_not_found", message="Product not found", status_code=404
            )
        item = await self._repository.get_item_for_product(
            empresa_id=tenant.empresa_id, product_id=product_id
        )
        summary = self._build_summary(product=product, item=item)
        movements, _ = await self._repository.list_movements(
            empresa_id=tenant.empresa_id, product_id=product_id, limit=50, offset=0
        )
        reservations, _ = await self._repository.list_reservations(
            empresa_id=tenant.empresa_id,
            product_id=product_id,
            status="active",
            limit=50,
            offset=0,
        )
        metrics = await self._build_metrics(tenant=tenant)
        return InventoryProductDetailResponse(
            product=summary,
            recent_movements=[InventoryMovementResponse.model_validate(m) for m in movements],
            active_reservations=[
                InventoryReservationResponse.model_validate(r) for r in reservations
            ],
            metrics=metrics,
        )

    async def update_item(
        self,
        *,
        tenant: TenantContext,
        product_id: UUID,
        payload: InventoryItemUpdateRequest,
    ) -> InventoryItemResponse:
        product = await self._repository.get_product_for_inventory(
            empresa_id=tenant.empresa_id, product_id=product_id
        )
        if product is None:
            raise AppError(
                code="product_not_found", message="Product not found", status_code=404
            )

        if (
            payload.stock_actual is not None
            and payload.stock_minimo is not None
            and payload.stock_actual < 0
        ):
            raise AppError(
                code="invalid_stock",
                message="Stock cannot be negative",
                status_code=422,
            )

        item = await self._repository.upsert_item(
            empresa_id=tenant.empresa_id,
            product_id=product_id,
            stock_actual=payload.stock_actual,
            stock_minimo=payload.stock_minimo,
        )
        if payload.stock_actual is not None and payload.motivo:
            await self._repository.record_movement(
                empresa_id=tenant.empresa_id,
                product_id=product_id,
                tipo=MovementType.AJUSTE.value,
                cantidad=payload.stock_actual,
                motivo=payload.motivo,
                ref_type="manual",
                ref_id=None,
            )
            item.last_movement_at = datetime.now(UTC)
        await self._repository.commit()
        await self._repository.refresh(item)
        return self._build_item_response(item=item)

    async def create_reservation(
        self,
        *,
        tenant: TenantContext,
        payload: InventoryReservationCreateRequest,
    ) -> InventoryReservationResponse:
        item = await self._repository.get_item_or_404(
            empresa_id=tenant.empresa_id, product_id=payload.product_id
        )
        if item.stock_disponible < payload.quantity:
            raise AppError(
                code="insufficient_stock",
                message="Not enough available stock to reserve",
                status_code=422,
            )
        item.stock_reservado = item.stock_reservado + payload.quantity
        item.last_movement_at = datetime.now(UTC)
        reservation = await self._repository.create_reservation(
            empresa_id=tenant.empresa_id,
            product_id=payload.product_id,
            quantity=payload.quantity,
            ref_type=payload.ref_type,
            ref_id=payload.ref_id,
            expires_at=payload.expires_at,
        )
        await self._repository.record_movement(
            empresa_id=tenant.empresa_id,
            product_id=payload.product_id,
            tipo=MovementType.RESERVA.value,
            cantidad=payload.quantity,
            motivo="reservation",
            ref_type=payload.ref_type or "manual",
            ref_id=reservation.id,
        )
        await self._repository.commit()
        await self._repository.refresh(reservation)
        return InventoryReservationResponse.model_validate(reservation)

    async def cancel_reservation(
        self, *, tenant: TenantContext, reservation_id: UUID
    ) -> InventoryReservationResponse:
        reservation = await self._repository.get_reservation(
            empresa_id=tenant.empresa_id, reservation_id=reservation_id
        )
        if reservation is None:
            raise AppError(
                code="reservation_not_found",
                message="Reservation not found",
                status_code=404,
            )
        if reservation.status != "active":
            raise AppError(
                code="reservation_not_active",
                message=f"Reservation already {reservation.status}",
                status_code=409,
            )
        item = await self._repository.get_item_for_product(
            empresa_id=tenant.empresa_id, product_id=reservation.product_id
        )
        if item is not None:
            item.stock_reservado = max(0, item.stock_reservado - reservation.quantity)
            item.last_movement_at = datetime.now(UTC)
        reservation.status = "cancelled"
        await self._repository.record_movement(
            empresa_id=tenant.empresa_id,
            product_id=reservation.product_id,
            tipo=MovementType.LIBERACION.value,
            cantidad=reservation.quantity,
            motivo="reservation_cancelled",
            ref_type="reservation",
            ref_id=reservation.id,
        )
        await self._repository.commit()
        await self._repository.refresh(reservation)
        return InventoryReservationResponse.model_validate(reservation)

    async def get_metrics(self, *, tenant: TenantContext) -> InventoryAggregateMetrics:
        return await self._build_metrics(tenant=tenant)

    # ------------------------------------------------------------------
    # Integration with the order events bus
    # ------------------------------------------------------------------

    async def handle_order_event(
        self,
        *,
        empresa_id: UUID,
        order_id: UUID,
        order_number: str,
        status: str,
        items: list[dict[str, Any]],
    ) -> None:
        """React to ``order.confirmed`` / ``order.cancelled`` events.

        For confirmed orders, deduct stock and record a ``salida``
        movement per item. For cancelled orders, the reverse
        (``entrada``) — restoring previously deducted stock.
        """
        if status == "confirmed":
            tipo = MovementType.SALIDA.value
            motivo = f"Order {order_number} confirmed"
        elif status == "cancelled":
            tipo = MovementType.ENTRADA.value
            motivo = f"Order {order_number} cancelled — restock"
        else:
            return

        for item in items:
            product_id = item.get("product_id")
            qty = int(item.get("quantity") or 0)
            if not product_id or qty <= 0:
                continue
            try:
                pid = UUID(str(product_id))
            except (TypeError, ValueError):
                continue
            await self._apply_order_movement(
                empresa_id=empresa_id,
                product_id=pid,
                tipo=tipo,
                cantidad=qty,
                motivo=motivo,
                ref_type="order",
                ref_id=order_id,
            )

        try:
            await self._repository.commit()
        except Exception:  # noqa: BLE001
            logger.exception("Failed to commit inventory reaction for order %s", order_id)
            await self._repository.rollback()

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    async def _apply_order_movement(
        self,
        *,
        empresa_id: UUID,
        product_id: UUID,
        tipo: str,
        cantidad: int,
        motivo: str,
        ref_type: str,
        ref_id: UUID,
    ) -> None:
        item = await self._repository.get_item_for_product(
            empresa_id=empresa_id, product_id=product_id
        )
        if item is None:
            # No inventory record for this product — auto-create at 0
            # so the movement can still be recorded for traceability.
            item = await self._repository.upsert_item(
                empresa_id=empresa_id,
                product_id=product_id,
                stock_actual=0,
                stock_minimo=0,
            )

        if tipo == MovementType.SALIDA.value:
            if item.stock_actual < cantidad:
                logger.warning(
                    "Insufficient stock for product %s (have %s, need %s). Clamping to available.",
                    product_id,
                    item.stock_actual,
                    cantidad,
                )
                cantidad = max(0, item.stock_actual)
            if cantidad == 0:
                return
            item.stock_actual = item.stock_actual - cantidad
        elif tipo == MovementType.ENTRADA.value:
            item.stock_actual = item.stock_actual + cantidad

        item.last_movement_at = datetime.now(UTC)
        await self._repository.record_movement(
            empresa_id=empresa_id,
            product_id=product_id,
            tipo=tipo,
            cantidad=cantidad,
            motivo=motivo,
            ref_type=ref_type,
            ref_id=ref_id,
        )

    async def _build_metrics(
        self, *, tenant: TenantContext
    ) -> InventoryAggregateMetrics:
        agg = await self._repository.aggregate_metrics(empresa_id=tenant.empresa_id)
        top = await self._repository.top_selling(empresa_id=tenant.empresa_id, limit=5)
        low = await self._repository.lowest_stock(empresa_id=tenant.empresa_id, limit=5)
        return InventoryAggregateMetrics(
            total_products=agg["total_products"],
            out_of_stock=agg["out_of_stock"],
            low_stock=agg["low_stock"],
            normal_stock=agg["normal_stock"],
            inventory_value=agg["inventory_value"],
            total_units=agg["total_units"],
            total_reserved_units=agg["total_reserved_units"],
            top_selling_products=[
                InventoryTopProductMetric(
                    product_id=item["product_id"],
                    name=item["name"],
                    units_sold=item["units_sold"],
                    revenue=item["revenue"],
                )
                for item in top
            ],
            lowest_stock_products=[
                InventoryLowStockProduct(
                    product_id=item["product_id"],
                    name=item["name"],
                    stock_actual=item["stock_actual"],
                    stock_minimo=item["stock_minimo"],
                    status=item["status"],
                )
                for item in low
            ],
        )

    def _build_summary(
        self, *, product: Producto, item
    ) -> InventoryProductSummary:
        stock_actual = int(item.stock_actual) if item else 0
        stock_minimo = int(item.stock_minimo) if item else 0
        stock_reservado = int(item.stock_reservado) if item else 0
        status = classify_status(stock_actual=stock_actual, stock_minimo=stock_minimo)
        sku = None
        image_url = None
        if product.variants:
            first_variant = product.variants[0]
            sku = first_variant.sku
        if product.images:
            image_url = product.images[0].image_url
        return InventoryProductSummary(
            product_id=product.id,
            name=product.name,
            category=product.category,
            base_price=product.base_price,
            sku=sku,
            image_url=image_url,
            stock_actual=stock_actual,
            stock_minimo=stock_minimo,
            stock_reservado=stock_reservado,
            stock_disponible=max(0, stock_actual - stock_reservado),
            status=status,
            last_movement_at=item.last_movement_at if item else None,
            updated_at=item.updated_at if item else product.updated_at,
        )

    def _build_item_response(self, *, item) -> InventoryItemResponse:
        stock_actual = int(item.stock_actual)
        stock_minimo = int(item.stock_minimo)
        stock_reservado = int(item.stock_reservado)
        return InventoryItemResponse(
            product_id=item.product_id,
            stock_actual=stock_actual,
            stock_minimo=stock_minimo,
            stock_reservado=stock_reservado,
            stock_disponible=max(0, stock_actual - stock_reservado),
            status=classify_status(stock_actual=stock_actual, stock_minimo=stock_minimo),
            last_movement_at=item.last_movement_at,
            updated_at=item.updated_at,
        )
