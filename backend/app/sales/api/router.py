from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.core.security.dependencies import TenantContext
from app.core.security.permissions import require_permission
from app.sales.api.dependencies import get_sales_api_service
from app.sales.api.schemas import (
    AnalyzeMessageRequest,
    AnalyzeMessageResponse,
    CustomerSalesProfileResponse,
    SalesActivityResponse,
    SalesInsightsResponse,
    SalesRecommendationsResponse,
    TopLeadsResponse,
)
from app.sales.api.service import SalesAPIService

router = APIRouter()


@router.get("/insights", response_model=SalesInsightsResponse)
async def get_insights(
    tenant: Annotated[TenantContext, Depends(require_permission("sales:read"))],
    service: Annotated[SalesAPIService, Depends(get_sales_api_service)],
) -> SalesInsightsResponse:
    return await service.get_insights(tenant=tenant)


@router.get("/customers/{customer_id}", response_model=CustomerSalesProfileResponse)
async def get_customer_sales_profile(
    customer_id: UUID,
    tenant: Annotated[TenantContext, Depends(require_permission("sales:read"))],
    service: Annotated[SalesAPIService, Depends(get_sales_api_service)],
) -> CustomerSalesProfileResponse:
    return await service.get_customer_profile(tenant=tenant, customer_id=customer_id)


@router.post("/analyze-message", response_model=AnalyzeMessageResponse)
async def analyze_message(
    payload: AnalyzeMessageRequest,
    tenant: Annotated[TenantContext, Depends(require_permission("sales:read"))],
    service: Annotated[SalesAPIService, Depends(get_sales_api_service)],
) -> AnalyzeMessageResponse:
    return await service.analyze_message(
        tenant=tenant,
        customer_id=UUID(payload.customer_id),
        message=payload.message,
    )


@router.get("/recommendations", response_model=SalesRecommendationsResponse)
async def get_recommendations(
    tenant: Annotated[TenantContext, Depends(require_permission("sales:read"))],
    service: Annotated[SalesAPIService, Depends(get_sales_api_service)],
) -> SalesRecommendationsResponse:
    return await service.get_recommendations(tenant=tenant)


@router.get("/top-leads", response_model=TopLeadsResponse)
async def get_top_leads(
    tenant: Annotated[TenantContext, Depends(require_permission("sales:read"))],
    service: Annotated[SalesAPIService, Depends(get_sales_api_service)],
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> TopLeadsResponse:
    return await service.get_top_leads(tenant=tenant, limit=limit)


@router.get("/activity", response_model=SalesActivityResponse)
async def get_activity(
    tenant: Annotated[TenantContext, Depends(require_permission("sales:read"))],
    service: Annotated[SalesAPIService, Depends(get_sales_api_service)],
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> SalesActivityResponse:
    return await service.get_activity(tenant=tenant, limit=limit)
