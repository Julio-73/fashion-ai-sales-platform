"""REST router for the Inventory Management module."""
from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.core.security.dependencies import TenantContext
from app.core.security.permissions import require_permission
from app.modules.inventory.dependencies import get_inventory_service
from app.modules.inventory.schemas import (
    InventoryAggregateMetrics,
    InventoryItemResponse,
    InventoryItemUpdateRequest,
    InventoryListResponse,
    InventoryProductDetailResponse,
    InventoryReservationCreateRequest,
    InventoryReservationResponse,
    InventorySortBy,
    InventoryStatusFilter,
)
from app.modules.inventory.service import InventoryService

router = APIRouter()


@router.get("/metrics", response_model=InventoryAggregateMetrics)
async def get_inventory_metrics(
    tenant: Annotated[TenantContext, Depends(require_permission("products:read"))],
    service: Annotated[InventoryService, Depends(get_inventory_service)],
) -> InventoryAggregateMetrics:
    return await service.get_metrics(tenant=tenant)


@router.get("", response_model=InventoryListResponse)
async def list_inventory(
    tenant: Annotated[TenantContext, Depends(require_permission("products:read"))],
    service: Annotated[InventoryService, Depends(get_inventory_service)],
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
    offset: Annotated[int, Query(ge=0)] = 0,
    search: Annotated[str | None, Query(min_length=1, max_length=120)] = None,
    category: Annotated[str | None, Query(max_length=80)] = None,
    status: Annotated[InventoryStatusFilter, Query()] = "all",
    sort_by: Annotated[InventorySortBy, Query()] = "name",
    sort_dir: Annotated[str, Query(pattern="^(asc|desc)$")] = "asc",
) -> InventoryListResponse:
    return await service.list_inventory(
        tenant=tenant,
        limit=limit,
        offset=offset,
        search=search,
        category=category,
        status=status,
        sort_by=sort_by,
        sort_dir=sort_dir,
    )


@router.get("/{product_id}", response_model=InventoryProductDetailResponse)
async def get_inventory_product(
    product_id: UUID,
    tenant: Annotated[TenantContext, Depends(require_permission("products:read"))],
    service: Annotated[InventoryService, Depends(get_inventory_service)],
) -> InventoryProductDetailResponse:
    return await service.get_product_detail(tenant=tenant, product_id=product_id)


@router.patch("/{product_id}", response_model=InventoryItemResponse)
async def update_inventory_item(
    product_id: UUID,
    payload: InventoryItemUpdateRequest,
    tenant: Annotated[TenantContext, Depends(require_permission("products:write"))],
    service: Annotated[InventoryService, Depends(get_inventory_service)],
) -> InventoryItemResponse:
    return await service.update_item(
        tenant=tenant, product_id=product_id, payload=payload
    )


@router.post(
    "/reservations",
    response_model=InventoryReservationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_inventory_reservation(
    payload: InventoryReservationCreateRequest,
    tenant: Annotated[TenantContext, Depends(require_permission("products:write"))],
    service: Annotated[InventoryService, Depends(get_inventory_service)],
) -> InventoryReservationResponse:
    return await service.create_reservation(tenant=tenant, payload=payload)


@router.delete(
    "/reservations/{reservation_id}",
    response_model=InventoryReservationResponse,
)
async def cancel_inventory_reservation(
    reservation_id: UUID,
    tenant: Annotated[TenantContext, Depends(require_permission("products:write"))],
    service: Annotated[InventoryService, Depends(get_inventory_service)],
) -> InventoryReservationResponse:
    return await service.cancel_reservation(
        tenant=tenant, reservation_id=reservation_id
    )
