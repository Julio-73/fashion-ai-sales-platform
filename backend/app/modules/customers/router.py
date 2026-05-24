from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.core.security.dependencies import TenantContext
from app.core.security.permissions import require_permission
from app.modules.customers.dependencies import get_customer_service
from app.modules.customers.schemas import (
    CustomerCreateRequest,
    CustomerListResponse,
    CustomerResponse,
    CustomerUpdateRequest,
    LeadStatus,
)
from app.modules.customers.service import CustomerService

router = APIRouter()


@router.get("", response_model=CustomerListResponse)
async def list_customers(
    tenant: Annotated[TenantContext, Depends(require_permission("customers:read"))],
    service: Annotated[CustomerService, Depends(get_customer_service)],
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
    offset: Annotated[int, Query(ge=0)] = 0,
    search: Annotated[str | None, Query(min_length=1, max_length=120)] = None,
    lead_status: LeadStatus | None = None,
) -> CustomerListResponse:
    return await service.list_customers(
        tenant=tenant,
        limit=limit,
        offset=offset,
        search=search,
        lead_status=lead_status,
    )


@router.post("", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
async def create_customer(
    payload: CustomerCreateRequest,
    tenant: Annotated[TenantContext, Depends(require_permission("customers:write"))],
    service: Annotated[CustomerService, Depends(get_customer_service)],
) -> CustomerResponse:
    return await service.create_customer(tenant=tenant, payload=payload)


@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: UUID,
    tenant: Annotated[TenantContext, Depends(require_permission("customers:read"))],
    service: Annotated[CustomerService, Depends(get_customer_service)],
) -> CustomerResponse:
    return await service.get_customer(tenant=tenant, customer_id=customer_id)


@router.patch("/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: UUID,
    payload: CustomerUpdateRequest,
    tenant: Annotated[TenantContext, Depends(require_permission("customers:write"))],
    service: Annotated[CustomerService, Depends(get_customer_service)],
) -> CustomerResponse:
    return await service.update_customer(tenant=tenant, customer_id=customer_id, payload=payload)


@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_customer(
    customer_id: UUID,
    tenant: Annotated[TenantContext, Depends(require_permission("customers:write"))],
    service: Annotated[CustomerService, Depends(get_customer_service)],
) -> None:
    await service.delete_customer(tenant=tenant, customer_id=customer_id)

