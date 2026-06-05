"""FastAPI router — executive dashboard module.

Single endpoint ``GET /`` mounted under ``/executive-dashboard`` (see
``app/api/router.py``). Returns the complete ``ExecutiveDashboardResponse``
payload for the authenticated tenant.
"""
from __future__ import annotations

from fastapi import APIRouter

from app.modules.executive_dashboard.dependencies import (
    ExecutiveDashboardReadContext,
    ExecutiveDashboardServiceDep,
)
from app.modules.executive_dashboard.schemas import ExecutiveDashboardResponse


router = APIRouter()


@router.get(
    "/",
    response_model=ExecutiveDashboardResponse,
    summary="Get the full executive dashboard payload for the current tenant",
)
async def get_executive_dashboard(
    tenant: ExecutiveDashboardReadContext,
    service: ExecutiveDashboardServiceDep,
) -> ExecutiveDashboardResponse:
    return await service.get_dashboard(tenant_id=tenant.empresa_id)
