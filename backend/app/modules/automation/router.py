"""FastAPI router — automation module.

All endpoints live under ``/automation`` (configured in
``app/api/router.py``).
"""
from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Query, status

from app.modules.automation.dependencies import (
    AutomationReadContext,
    AutomationWriteContext,
    DB,
)
from app.modules.automation.schemas import (
    AutomationEventResponse,
    AutomationMetricsResponse,
    AutomationRuleResponse,
    AutomationRuleUpdate,
    AutomationTaskCreate,
    AutomationTaskResponse,
    AutomationTaskUpdate,
    CalendarView,
    TaskBoardResponse,
)
from app.modules.automation.service import AutomationService


router = APIRouter()


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------
@router.get(
    "/rules",
    response_model=list[AutomationRuleResponse],
    summary="List automation rules for the tenant",
)
async def list_rules(
    db: DB,
    _: AutomationReadContext,
    enabled: bool | None = Query(default=None),
) -> list[AutomationRuleResponse]:
    svc = AutomationService(db)
    return await svc.list_rules(_.empresa_id, enabled=enabled)


@router.post(
    "/rules/seed",
    response_model=list[AutomationRuleResponse],
    summary="Seed the 7 default rules for the tenant (idempotent)",
    status_code=status.HTTP_200_OK,
)
async def seed_rules(
    db: DB,
    _: AutomationWriteContext,
) -> list[AutomationRuleResponse]:
    svc = AutomationService(db)
    return await svc.ensure_seeded(_.empresa_id)


@router.patch(
    "/rules/{rule_id}",
    response_model=AutomationRuleResponse,
    summary="Update an automation rule",
)
async def update_rule(
    rule_id: UUID,
    payload: AutomationRuleUpdate,
    db: DB,
    _: AutomationWriteContext,
) -> AutomationRuleResponse:
    svc = AutomationService(db)
    changes: dict[str, Any] = payload.model_dump(exclude_unset=True)
    return await svc.update_rule(_.empresa_id, rule_id, changes)


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------
@router.post(
    "/run",
    summary="Run the rule engine once for the tenant (returns scan stats)",
)
async def run_engine(
    db: DB,
    _: AutomationWriteContext,
) -> dict[str, Any]:
    svc = AutomationService(db)
    stats = await svc.run_engine(_.empresa_id)
    return {
        "scanned_customers": stats.scanned_customers,
        "scanned_deals": stats.scanned_deals,
        "scanned_orders": stats.scanned_orders,
        "scanned_inventory": stats.scanned_inventory,
        "tasks_created": stats.tasks_created,
        "tasks_updated": stats.tasks_updated,
        "events_created": stats.events_created,
        "rules_skipped": list(stats.rules_skipped),
    }


# ---------------------------------------------------------------------------
# Tasks
# ---------------------------------------------------------------------------
@router.get(
    "/tasks",
    response_model=list[AutomationTaskResponse],
    summary="List automation tasks",
)
async def list_tasks(
    db: DB,
    _: AutomationReadContext,
    status_filter: str | None = Query(default=None, alias="status"),
    priority: str | None = Query(default=None),
    task_type: str | None = Query(default=None),
    customer_id: UUID | None = Query(default=None),
    pipeline_item_id: UUID | None = Query(default=None),
    rule_id: UUID | None = Query(default=None),
    search: str | None = Query(default=None, max_length=200),
    due_before: datetime | None = Query(default=None),
    due_after: datetime | None = Query(default=None),
    limit: int = Query(default=200, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> list[AutomationTaskResponse]:
    svc = AutomationService(db)
    return await svc.list_tasks(
        _.empresa_id,
        status=status_filter,
        priority=priority,
        task_type=task_type,
        customer_id=customer_id,
        pipeline_item_id=pipeline_item_id,
        rule_id=rule_id,
        search=search,
        due_before=due_before,
        due_after=due_after,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/tasks/board",
    response_model=TaskBoardResponse,
    summary="Board projection for /dashboard/tasks",
)
async def tasks_board(
    db: DB,
    _: AutomationReadContext,
) -> TaskBoardResponse:
    svc = AutomationService(db)
    return await svc.board(_.empresa_id)


@router.get(
    "/tasks/{task_id}",
    response_model=AutomationTaskResponse,
    summary="Get a single task",
)
async def get_task(
    task_id: UUID,
    db: DB,
    _: AutomationReadContext,
) -> AutomationTaskResponse:
    svc = AutomationService(db)
    return await svc.get_task(_.empresa_id, task_id)


@router.post(
    "/tasks",
    response_model=AutomationTaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a task manually",
)
async def create_task(
    payload: AutomationTaskCreate,
    db: DB,
    _: AutomationWriteContext,
) -> AutomationTaskResponse:
    svc = AutomationService(db)
    return await svc.create_task(_.empresa_id, payload.model_dump())


@router.patch(
    "/tasks/{task_id}",
    response_model=AutomationTaskResponse,
    summary="Update a task",
)
async def update_task(
    task_id: UUID,
    payload: AutomationTaskUpdate,
    db: DB,
    _: AutomationWriteContext,
) -> AutomationTaskResponse:
    svc = AutomationService(db)
    changes = payload.model_dump(exclude_unset=True)
    return await svc.update_task(_.empresa_id, task_id, changes)


@router.post(
    "/tasks/{task_id}/complete",
    response_model=AutomationTaskResponse,
    summary="Mark a task as completed",
)
async def complete_task(
    task_id: UUID,
    db: DB,
    _: AutomationWriteContext,
) -> AutomationTaskResponse:
    svc = AutomationService(db)
    return await svc.complete_task(_.empresa_id, task_id)


@router.post(
    "/tasks/{task_id}/cancel",
    response_model=AutomationTaskResponse,
    summary="Cancel a task",
)
async def cancel_task(
    task_id: UUID,
    db: DB,
    _: AutomationWriteContext,
) -> AutomationTaskResponse:
    svc = AutomationService(db)
    return await svc.cancel_task(_.empresa_id, task_id)


# ---------------------------------------------------------------------------
# Calendar
# ---------------------------------------------------------------------------
@router.get(
    "/calendar",
    response_model=CalendarView,
    summary="Calendar projection for /dashboard/calendar",
)
async def calendar_view(
    db: DB,
    _: AutomationReadContext,
    view: str = Query(default="week", pattern="^(day|week|month)$"),
    anchor: datetime | None = Query(default=None),
) -> CalendarView:
    svc = AutomationService(db)
    return await svc.calendar(_.empresa_id, view=view, anchor=anchor)


# ---------------------------------------------------------------------------
# Events
# ---------------------------------------------------------------------------
@router.get(
    "/events",
    response_model=list[AutomationEventResponse],
    summary="List recent automation events",
)
async def list_events(
    db: DB,
    _: AutomationReadContext,
    rule_key: str | None = Query(default=None),
    entity_type: str | None = Query(default=None),
    severity: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
) -> list[AutomationEventResponse]:
    svc = AutomationService(db)
    return await svc.list_events(
        _.empresa_id,
        rule_key=rule_key,
        entity_type=entity_type,
        severity=severity,
        limit=limit,
    )


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------
@router.get(
    "/metrics",
    response_model=AutomationMetricsResponse,
    summary="Top-level metrics for the Alert Center + dashboards",
)
async def metrics(
    db: DB,
    _: AutomationReadContext,
) -> AutomationMetricsResponse:
    svc = AutomationService(db)
    return await svc.metrics(_.empresa_id)


__all__ = ["router"]
