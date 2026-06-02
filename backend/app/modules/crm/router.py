"""CRM Enterprise V1 — Customer 360 REST endpoints.

Mounted under ``/api/v1/crm``. All endpoints require the
``customers:read`` permission and are tenant-isolated.
"""
from __future__ import annotations

from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.core.security.dependencies import TenantContext
from app.core.security.permissions import require_permission
from app.modules.crm.dependencies import get_crm_service
from app.modules.crm.schemas import (
    Customer360ListResponse,
    Customer360Summary,
    CustomerAggregateMetrics,
    CustomerOrderHistoryResponse,
    CustomerSortBy,
    CustomerStatusFilter,
)
from app.modules.crm.service import CrmService

router = APIRouter()


@router.get("/metrics", response_model=CustomerAggregateMetrics)
async def get_crm_metrics(
    tenant: Annotated[TenantContext, Depends(require_permission("customers:read"))],
    service: Annotated[CrmService, Depends(get_crm_service)],
) -> CustomerAggregateMetrics:
    return await service.get_metrics(tenant=tenant)


@router.get("/customers", response_model=Customer360ListResponse)
async def list_customer_360(
    tenant: Annotated[TenantContext, Depends(require_permission("customers:read"))],
    service: Annotated[CrmService, Depends(get_crm_service)],
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
    offset: Annotated[int, Query(ge=0)] = 0,
    search: Annotated[str | None, Query(min_length=1, max_length=120)] = None,
    status: Annotated[CustomerStatusFilter, Query()] = "all",
    is_vip: Annotated[bool | None, Query()] = None,
    is_recurrent: Annotated[bool | None, Query()] = None,
    date_from: Annotated[date | None, Query()] = None,
    date_to: Annotated[date | None, Query()] = None,
    sort_by: Annotated[CustomerSortBy, Query()] = "created_at",
    sort_dir: Annotated[str, Query(pattern="^(asc|desc)$")] = "desc",
) -> Customer360ListResponse:
    return await service.list_customer_360(
        tenant=tenant,
        limit=limit,
        offset=offset,
        search=search,
        is_vip=is_vip,
        is_recurrent=is_recurrent,
        date_from=date_from,
        date_to=date_to,
        sort_by=sort_by,
        sort_dir=sort_dir,
        status_filter=status,
    )


@router.get("/customers/{customer_id}", response_model=Customer360Summary)
async def get_customer_360(
    customer_id: UUID,
    tenant: Annotated[TenantContext, Depends(require_permission("customers:read"))],
    service: Annotated[CrmService, Depends(get_crm_service)],
) -> Customer360Summary:
    return await service.get_customer_360(tenant=tenant, customer_id=customer_id)


@router.get("/customers/{customer_id}/orders", response_model=CustomerOrderHistoryResponse)
async def list_customer_orders(
    customer_id: UUID,
    tenant: Annotated[TenantContext, Depends(require_permission("customers:read"))],
    service: Annotated[CrmService, Depends(get_crm_service)],
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> CustomerOrderHistoryResponse:
    return await service.list_customer_orders(
        tenant=tenant,
        customer_id=customer_id,
        limit=limit,
        offset=offset,
    )
