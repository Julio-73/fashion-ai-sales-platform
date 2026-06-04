"""FastAPI router — pipeline module.

All endpoints live under ``/pipeline`` (configured in
``app/api/router.py``). Auth is handled by the dependencies module.
"""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Query, status

from app.modules.pipeline.dependencies import (
    DB,
    PipelineMetricsContext,
    PipelineReadContext,
    PipelineWriteContext,
)
from app.modules.pipeline.schemas import (
    PipelineAIScoreResponse,
    PipelineAlertsResponse,
    PipelineBoardResponse,
    PipelineDashboardResponse,
    PipelineFunnelResponse,
    PipelineItemCreate,
    PipelineItemMoveStage,
    PipelineItemResponse,
    PipelineItemUpdate,
    PipelineMetricsResponse,
    PipelineRecommendation,
    PipelineRecommendationsResponse,
    PipelineStageInfo,
)
from app.modules.pipeline.service import PipelineService


router = APIRouter()


# ---------------------------------------------------------------------------
# Catalog & static info
# ---------------------------------------------------------------------------
@router.get(
    "/stages",
    response_model=list[PipelineStageInfo],
    summary="List pipeline stages with metadata",
)
async def get_stages(_: PipelineReadContext) -> list[PipelineStageInfo]:
    return PipelineService.list_stages()


@router.get(
    "/board",
    response_model=PipelineBoardResponse,
    summary="List all deals (kanban view)",
)
async def get_board(
    db: DB,
    _: PipelineReadContext,
    stage: str | None = Query(default=None, description="Filter by stage key"),
    is_open: bool | None = Query(default=None, description="True=open, False=closed"),
    search: str | None = Query(default=None, max_length=200),
) -> PipelineBoardResponse:
    svc = PipelineService(db)
    return await svc.list_board(_.empresa_id, stage=stage, is_open=is_open, search=search)


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------
@router.post(
    "/deals",
    response_model=PipelineItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new deal",
)
async def create_deal(
    payload: PipelineItemCreate,
    db: DB,
    _: PipelineWriteContext,
) -> PipelineItemResponse:
    svc = PipelineService(db)
    return await svc.create(_.empresa_id, payload)


@router.get(
    "/deals/{deal_id}",
    response_model=PipelineItemResponse,
    summary="Get a single deal (with AI score)",
)
async def get_deal(
    deal_id: UUID,
    db: DB,
    _: PipelineReadContext,
) -> PipelineItemResponse:
    svc = PipelineService(db)
    return await svc.get(_.empresa_id, deal_id)


@router.patch(
    "/deals/{deal_id}",
    response_model=PipelineItemResponse,
    summary="Update deal fields",
)
async def update_deal(
    deal_id: UUID,
    payload: PipelineItemUpdate,
    db: DB,
    _: PipelineWriteContext,
) -> PipelineItemResponse:
    svc = PipelineService(db)
    return await svc.update(_.empresa_id, deal_id, payload)


@router.delete(
    "/deals/{deal_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a deal",
)
async def delete_deal(
    deal_id: UUID,
    db: DB,
    _: PipelineWriteContext,
) -> None:
    svc = PipelineService(db)
    await svc.delete(_.empresa_id, deal_id)


@router.post(
    "/deals/{deal_id}/move-stage",
    response_model=PipelineItemResponse,
    summary="Move a deal to another stage",
)
async def move_stage(
    deal_id: UUID,
    payload: PipelineItemMoveStage,
    db: DB,
    _: PipelineWriteContext,
) -> PipelineItemResponse:
    svc = PipelineService(db)
    return await svc.move_stage(_.empresa_id, deal_id, payload)


# ---------------------------------------------------------------------------
# Analytics
# ---------------------------------------------------------------------------
@router.get(
    "/metrics",
    response_model=PipelineMetricsResponse,
    summary="Aggregate metrics for the funnel",
)
async def get_metrics(
    db: DB,
    _: PipelineMetricsContext,
) -> PipelineMetricsResponse:
    svc = PipelineService(db)
    return await svc.metrics(_.empresa_id)


@router.get(
    "/funnel",
    response_model=PipelineFunnelResponse,
    summary="Funnel data for the dashboard visual",
)
async def get_funnel(
    db: DB,
    _: PipelineReadContext,
) -> PipelineFunnelResponse:
    svc = PipelineService(db)
    return await svc.funnel(_.empresa_id)


@router.get(
    "/alerts",
    response_model=PipelineAlertsResponse,
    summary="Active automation alerts",
)
async def get_alerts(
    db: DB,
    _: PipelineReadContext,
) -> PipelineAlertsResponse:
    svc = PipelineService(db)
    return await svc.alerts(_.empresa_id)


@router.get(
    "/recommendations",
    response_model=PipelineRecommendationsResponse,
    summary="AI recommendations for every open deal",
)
async def get_recommendations(
    db: DB,
    _: PipelineReadContext,
) -> PipelineRecommendationsResponse:
    svc = PipelineService(db)
    return await svc.recommendations(_.empresa_id)


@router.post(
    "/deals/{deal_id}/ai-score",
    response_model=PipelineAIScoreResponse,
    summary="Compute (or recompute) the AI score for a deal",
)
async def score_deal(
    deal_id: UUID,
    db: DB,
    _: PipelineReadContext,
) -> PipelineAIScoreResponse:
    svc = PipelineService(db)
    return await svc.score(_.empresa_id, deal_id)


@router.get(
    "/dashboard",
    response_model=PipelineDashboardResponse,
    summary="Full dashboard payload (metrics + funnel + alerts + top deals)",
)
async def get_dashboard(
    db: DB,
    _: PipelineReadContext,
) -> PipelineDashboardResponse:
    svc = PipelineService(db)
    return await svc.dashboard(_.empresa_id)


__all__ = ["router"]
