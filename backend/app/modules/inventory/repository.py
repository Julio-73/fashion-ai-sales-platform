"""Repository for the Inventory Management module."""
from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import and_, case, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.inventory.models import (
    InventoryItem,
    InventoryMovement,
    InventoryReservation,
)
from app.modules.inventory.schemas import (
    InventoryStatusFilter,
    classify_status,
)
from app.modules.products.models import Producto


class InventoryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ------------------------------------------------------------------
    # Items
    # ------------------------------------------------------------------

    async def get_item_for_product(
        self, *, empresa_id: UUID, product_id: UUID
    ) -> InventoryItem | None:
        result = await self._session.execute(
            select(InventoryItem).where(
                InventoryItem.empresa_id == empresa_id,
                InventoryItem.product_id == product_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_items_for_products(
        self, *, empresa_id: UUID, product_ids: Sequence[UUID],
    ) -> Sequence[InventoryItem]:
        """Batch lookup (H-1).

        Returns the inventory rows for ``product_ids`` in a single query.
        Used by ``handle_order_event`` so that processing a 10-item order
        triggers 1 SELECT instead of N.
        """
        if not product_ids:
            return []
        result = await self._session.execute(
            select(InventoryItem).where(
                InventoryItem.empresa_id == empresa_id,
                InventoryItem.product_id.in_(product_ids),
            )
        )
        return result.scalars().all()

    async def get_item_or_404(
        self, *, empresa_id: UUID, product_id: UUID
    ) -> InventoryItem:
        item = await self.get_item_for_product(empresa_id=empresa_id, product_id=product_id)
        if item is None:
            from app.core.errors import AppError

            raise AppError(
                code="inventory_item_not_found",
                message="No inventory record exists for this product",
                status_code=404,
            )
        return item

    async def upsert_item(
        self,
        *,
        empresa_id: UUID,
        product_id: UUID,
        stock_actual: int | None = None,
        stock_minimo: int | None = None,
        stock_reservado: int | None = None,
        last_movement_at=None,
    ) -> InventoryItem:
        item = await self.get_item_for_product(empresa_id=empresa_id, product_id=product_id)
        if item is None:
            item = InventoryItem(
                empresa_id=empresa_id,
                product_id=product_id,
                stock_actual=stock_actual or 0,
                stock_minimo=stock_minimo or 0,
                stock_reservado=stock_reservado or 0,
                last_movement_at=last_movement_at,
            )
            self._session.add(item)
        else:
            if stock_actual is not None:
                item.stock_actual = stock_actual
            if stock_minimo is not None:
                item.stock_minimo = stock_minimo
            if stock_reservado is not None:
                item.stock_reservado = stock_reservado
            if last_movement_at is not None:
                item.last_movement_at = last_movement_at
        await self._session.flush()
        return item

    async def list_with_product(
        self,
        *,
        empresa_id: UUID,
        limit: int,
        offset: int,
        search: str | None,
        category: str | None,
        status: InventoryStatusFilter,
        sort_by: str,
        sort_dir: str,
    ) -> tuple[Sequence[tuple[Producto, InventoryItem | None]], int]:
        # H-2: classify stock status in SQL so pagination is consistent
        # and the ``total`` reflects the filtered count.
        # classify_status in app/modules/inventory/schemas.py is:
        #   stock_actual <= 0           -> 'agotado'
        #   stock_actual <= stock_minimo -> 'stock_bajo'
        #   else                        -> 'normal'
        stock_actual = func.coalesce(InventoryItem.stock_actual, 0)
        stock_minimo = func.coalesce(InventoryItem.stock_minimo, 0)
        if status == "agotado":
            status_filter = stock_actual <= 0
        elif status == "stock_bajo":
            status_filter = (stock_actual > 0) & (stock_actual <= stock_minimo)
        elif status == "normal":
            status_filter = stock_actual > stock_minimo
        else:
            status_filter = None

        query = (
            select(Producto, InventoryItem)
            .options(selectinload(Producto.variants), selectinload(Producto.images))
            .outerjoin(
                InventoryItem,
                and_(
                    InventoryItem.product_id == Producto.id,
                    InventoryItem.empresa_id == empresa_id,
                ),
            )
            .where(Producto.empresa_id == empresa_id, Producto.deleted_at.is_(None))
        )
        if category:
            query = query.where(Producto.category == category)
        if search:
            pattern = f"%{search.strip()}%"
            query = query.where(
                or_(
                    Producto.name.ilike(pattern),
                    Producto.slug.ilike(pattern),
                    Producto.category.ilike(pattern),
                )
            )
        if status_filter is not None:
            query = query.where(status_filter)

        # ``total`` now reflects the post-filter count (H-2).
        items_total_q = select(func.count()).select_from(query.subquery())
        items_total = int((await self._session.execute(items_total_q)).scalar_one())

        # Order by (defaults to name asc) â€” for numeric columns we cast.
        sort_column = {
            "name": Producto.name,
            "stock_actual": stock_actual,
            "stock_disponible": func.coalesce(InventoryItem.stock_actual - InventoryItem.stock_reservado, 0),
            "last_movement_at": InventoryItem.last_movement_at,
            "category": Producto.category,
        }.get(sort_by, Producto.name)
        if sort_dir == "desc":
            query = query.order_by(sort_column.desc().nullslast(), Producto.name.asc())
        else:
            query = query.order_by(sort_column.asc().nullsfirst(), Producto.name.asc())
        query = query.limit(limit).offset(offset)
        rows = (await self._session.execute(query)).all()

        return rows, items_total

    # ------------------------------------------------------------------
    # Movements
    # ------------------------------------------------------------------

    async def record_movement(
        self,
        *,
        empresa_id: UUID,
        product_id: UUID,
        tipo: str,
        cantidad: int,
        motivo: str | None = None,
        ref_type: str | None = None,
        ref_id: UUID | None = None,
    ) -> InventoryMovement:
        movement = InventoryMovement(
            empresa_id=empresa_id,
            product_id=product_id,
            tipo=tipo,
            cantidad=cantidad,
            motivo=motivo,
            ref_type=ref_type,
            ref_id=ref_id,
        )
        self._session.add(movement)
        await self._session.flush()
        return movement

    async def list_movements(
        self,
        *,
        empresa_id: UUID,
        product_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[Sequence[InventoryMovement], int]:
        base = select(InventoryMovement).where(
            InventoryMovement.empresa_id == empresa_id,
            InventoryMovement.product_id == product_id,
        )
        total = int(
            (
                await self._session.execute(
                    select(func.count()).select_from(base.subquery())
                )
            ).scalar_one()
        )
        result = await self._session.execute(
            base.order_by(InventoryMovement.created_at.desc()).limit(limit).offset(offset)
        )
        return result.scalars().all(), total

    # ------------------------------------------------------------------
    # Reservations
    # ------------------------------------------------------------------

    async def create_reservation(
        self,
        *,
        empresa_id: UUID,
        product_id: UUID,
        quantity: int,
        ref_type: str | None = None,
        ref_id: UUID | None = None,
        expires_at=None,
    ) -> InventoryReservation:
        reservation = InventoryReservation(
            empresa_id=empresa_id,
            product_id=product_id,
            quantity=quantity,
            status="active",
            ref_type=ref_type,
            ref_id=ref_id,
            expires_at=expires_at,
        )
        self._session.add(reservation)
        await self._session.flush()
        return reservation

    async def get_reservation(
        self, *, empresa_id: UUID, reservation_id: UUID
    ) -> InventoryReservation | None:
        result = await self._session.execute(
            select(InventoryReservation).where(
                InventoryReservation.empresa_id == empresa_id,
                InventoryReservation.id == reservation_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_reservations(
        self,
        *,
        empresa_id: UUID,
        product_id: UUID | None = None,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[Sequence[InventoryReservation], int]:
        query = select(InventoryReservation).where(
            InventoryReservation.empresa_id == empresa_id
        )
        if product_id:
            query = query.where(InventoryReservation.product_id == product_id)
        if status:
            query = query.where(InventoryReservation.status == status)
        total = int(
            (
                await self._session.execute(
                    select(func.count()).select_from(query.subquery())
                )
            ).scalar_one()
        )
        result = await self._session.execute(
            query.order_by(InventoryReservation.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all(), total

    # ------------------------------------------------------------------
    # Aggregates / metrics
    # ------------------------------------------------------------------

    async def aggregate_metrics(
        self, *, empresa_id: UUID
    ) -> dict[str, Any]:
        # Total products, units, reserved, value, status buckets.
        value_expr = func.coalesce(
            func.sum(
                InventoryItem.stock_actual
                * func.coalesce(Producto.base_price, 0)
            ),
            0,
        )
        units_expr = func.coalesce(func.sum(InventoryItem.stock_actual), 0)
        reserved_expr = func.coalesce(func.sum(InventoryItem.stock_reservado), 0)
        out_expr = func.coalesce(
            func.sum(case((InventoryItem.stock_actual <= 0, 1), else_=0)), 0
        )
        low_expr = func.coalesce(
            func.sum(
                case(
                    (
                        and_(
                            InventoryItem.stock_actual > 0,
                            InventoryItem.stock_actual <= InventoryItem.stock_minimo,
                        ),
                        1,
                    ),
                    else_=0,
                )
            ),
            0,
        )
        normal_expr = func.coalesce(
            func.sum(
                case(
                    (
                        InventoryItem.stock_actual > InventoryItem.stock_minimo,
                        1,
                    ),
                    else_=0,
                )
            ),
            0,
        )
        total_products = int(
            (
                await self._session.execute(
                    select(func.count()).select_from(Producto).where(
                        Producto.empresa_id == empresa_id,
                        Producto.deleted_at.is_(None),
                    )
                )
            ).scalar_one()
        )

        result = await self._session.execute(
            select(value_expr, units_expr, reserved_expr, out_expr, low_expr, normal_expr)
            .select_from(Producto)
            .outerjoin(
                InventoryItem,
                and_(
                    InventoryItem.product_id == Producto.id,
                    InventoryItem.empresa_id == empresa_id,
                ),
            )
            .where(Producto.empresa_id == empresa_id, Producto.deleted_at.is_(None))
        )
        value, units, reserved, out_of_stock, low_stock, normal_stock = result.one()
        return {
            "total_products": total_products,
            "out_of_stock": int(out_of_stock),
            "low_stock": int(low_stock),
            "normal_stock": int(normal_stock),
            "inventory_value": Decimal(value or 0),
            "total_units": int(units or 0),
            "total_reserved_units": int(reserved or 0),
        }

    async def top_selling(
        self, *, empresa_id: UUID, limit: int = 5
    ) -> list[dict[str, Any]]:
        from app.modules.orders.models import Order, OrderItem

        stmt = (
            select(
                Producto.id.label("product_id"),
                Producto.name.label("name"),
                func.coalesce(func.sum(OrderItem.quantity), 0).label("units_sold"),
                func.coalesce(func.sum(OrderItem.quantity * OrderItem.price), 0).label(
                    "revenue"
                ),
            )
            .select_from(Producto)
            .outerjoin(
                OrderItem,
                and_(
                    OrderItem.product_id == Producto.id,
                    OrderItem.empresa_id == empresa_id,
                ),
            )
            .outerjoin(Order, Order.id == OrderItem.order_id)
            .where(
                Producto.empresa_id == empresa_id,
                Producto.deleted_at.is_(None),
                or_(Order.status.is_(None), Order.status != "cancelled"),
            )
            .group_by(Producto.id, Producto.name)
            .order_by(func.coalesce(func.sum(OrderItem.quantity), 0).desc())
            .limit(limit)
        )
        rows = (await self._session.execute(stmt)).all()
        return [
            {
                "product_id": row.product_id,
                "name": row.name,
                "units_sold": int(row.units_sold or 0),
                "revenue": Decimal(row.revenue or 0),
            }
            for row in rows
        ]

    async def lowest_stock(
        self, *, empresa_id: UUID, limit: int = 5
    ) -> list[dict[str, Any]]:
        stmt = (
            select(
                Producto.id.label("product_id"),
                Producto.name.label("name"),
                func.coalesce(InventoryItem.stock_actual, 0).label("stock_actual"),
                func.coalesce(InventoryItem.stock_minimo, 0).label("stock_minimo"),
            )
            .select_from(Producto)
            .outerjoin(
                InventoryItem,
                and_(
                    InventoryItem.product_id == Producto.id,
                    InventoryItem.empresa_id == empresa_id,
                ),
            )
            .where(Producto.empresa_id == empresa_id, Producto.deleted_at.is_(None))
            .order_by(func.coalesce(InventoryItem.stock_actual, 0).asc())
            .limit(limit)
        )
        rows = (await self._session.execute(stmt)).all()
        return [
            {
                "product_id": row.product_id,
                "name": row.name,
                "stock_actual": int(row.stock_actual or 0),
                "stock_minimo": int(row.stock_minimo or 0),
                "status": classify_status(
                    stock_actual=int(row.stock_actual or 0),
                    stock_minimo=int(row.stock_minimo or 0),
                ),
            }
            for row in rows
        ]

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()

    async def refresh(self, item) -> None:
        await self._session.refresh(item)

    async def get_product_for_inventory(
        self, *, empresa_id: UUID, product_id: UUID
    ) -> Producto | None:
        result = await self._session.execute(
            select(Producto)
            .options(selectinload(Producto.variants), selectinload(Producto.images))
            .where(
                Producto.empresa_id == empresa_id,
                Producto.id == product_id,
                Producto.deleted_at.is_(None),
            )
        )
        return result.unique().scalar_one_or_none()

