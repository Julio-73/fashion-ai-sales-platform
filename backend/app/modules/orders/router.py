from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.core.security.dependencies import TenantContext
from app.core.security.permissions import require_permission
from app.modules.orders.dependencies import get_order_service
from app.modules.orders.schemas import (
    OrderCreateRequest,
    OrderListResponse,
    OrderMetricsResponse,
    OrderResponse,
    OrderStatus,
    OrderStatusUpdateRequest,
)
from app.modules.orders.service import OrderService

router = APIRouter()


@router.get("", response_model=OrderListResponse)
async def list_orders(
    tenant: Annotated[TenantContext, Depends(require_permission("orders:read"))],
    service: Annotated[OrderService, Depends(get_order_service)],
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
    offset: Annotated[int, Query(ge=0)] = 0,
    status: Annotated[OrderStatus | None, Query()] = None,
    customer: Annotated[str | None, Query(min_length=1, max_length=180)] = None,
    date_from: Annotated[date | None, Query()] = None,
    date_to: Annotated[date | None, Query()] = None,
) -> OrderListResponse:
    return await service.list_orders(
        tenant=tenant,
        limit=limit,
        offset=offset,
        status=status,
        customer=customer,
        date_from=date_from,
        date_to=date_to,
    )


@router.get("/metrics", response_model=OrderMetricsResponse)
async def get_order_metrics(
    tenant: Annotated[TenantContext, Depends(require_permission("orders:read"))],
    service: Annotated[OrderService, Depends(get_order_service)],
) -> OrderMetricsResponse:
    return await service.get_metrics(tenant=tenant)


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    payload: OrderCreateRequest,
    tenant: Annotated[TenantContext, Depends(require_permission("orders:write"))],
    service: Annotated[OrderService, Depends(get_order_service)],
) -> OrderResponse:
    return await service.create_order(tenant=tenant, payload=payload)


@router.patch("/{order_id}/status", response_model=OrderResponse)
async def update_order_status(
    order_id: UUID,
    payload: OrderStatusUpdateRequest,
    tenant: Annotated[TenantContext, Depends(require_permission("orders:write"))],
    service: Annotated[OrderService, Depends(get_order_service)],
) -> OrderResponse:
    return await service.update_status(tenant=tenant, order_id=order_id, status=payload.status)
