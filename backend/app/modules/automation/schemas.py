"""Pydantic schemas for the Automation Engine.

We keep the request/response surface narrow:

* rules CRUD     — admin endpoint
* tasks CRUD     — list / get / create / update / complete
* events         — read-only audit log
* metrics        — read-only
* calendar       — derived view of tasks with due_date
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.modules.automation.models import (
    EVENT_SEVERITY_VALUES,
    ENTITY_TYPE_VALUES,
    TASK_PRIORITY_VALUES,
    TASK_STATUS_VALUES,
    TASK_TYPE_VALUES,
)


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------
class AutomationRuleBase(BaseModel):
    rule_key: str = Field(..., min_length=2, max_length=64)
    name: str = Field(..., min_length=2, max_length=160)
    description: str | None = None
    trigger_type: str = Field(..., min_length=2, max_length=32)
    enabled: bool = True
    config: dict[str, Any] = Field(default_factory=dict)


class AutomationRuleCreate(AutomationRuleBase):
    pass


class AutomationRuleUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    enabled: bool | None = None
    config: dict[str, Any] | None = None


class AutomationRuleResponse(AutomationRuleBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    empresa_id: UUID
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Tasks
# ---------------------------------------------------------------------------
TaskStatus = Literal[tuple(TASK_STATUS_VALUES)]  # type: ignore[valid-type]
TaskPriority = Literal[tuple(TASK_PRIORITY_VALUES)]  # type: ignore[valid-type]
TaskType = Literal[tuple(TASK_TYPE_VALUES)]  # type: ignore[valid-type]
EventSeverity = Literal[tuple(EVENT_SEVERITY_VALUES)]  # type: ignore[valid-type]
EntityType = Literal[tuple(ENTITY_TYPE_VALUES)]  # type: ignore[valid-type]


class AutomationTaskBase(BaseModel):
    title: str = Field(..., min_length=2, max_length=200)
    description: str | None = None
    task_type: TaskType = "follow_up"
    priority: TaskPriority = "medium"
    status: TaskStatus = "pending"
    due_date: datetime | None = None


class AutomationTaskCreate(AutomationTaskBase):
    rule_id: UUID | None = None
    customer_id: UUID | None = None
    pipeline_item_id: UUID | None = None
    conversation_id: UUID | None = None
    ai_reason: str | None = None
    ai_next_action: str | None = None
    ai_score: int | None = Field(default=None, ge=0, le=100)


class AutomationTaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    priority: TaskPriority | None = None
    status: TaskStatus | None = None
    due_date: datetime | None = None
    ai_reason: str | None = None
    ai_next_action: str | None = None


class AutomationTaskResponse(AutomationTaskBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    empresa_id: UUID
    rule_id: UUID | None
    customer_id: UUID | None
    pipeline_item_id: UUID | None
    conversation_id: UUID | None
    ai_reason: str | None
    ai_next_action: str | None
    ai_score: int | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Events
# ---------------------------------------------------------------------------
class AutomationEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    empresa_id: UUID
    rule_id: UUID | None
    rule_key: str
    event_type: str
    entity_type: EntityType
    entity_id: UUID | None
    severity: EventSeverity
    payload: dict[str, Any]
    created_at: datetime


# ---------------------------------------------------------------------------
# Metrics + Calendar + Board
# ---------------------------------------------------------------------------
class AutomationMetricsResponse(BaseModel):
    tasks_total: int = 0
    tasks_pending: int = 0
    tasks_today: int = 0
    tasks_this_week: int = 0
    tasks_overdue: int = 0
    tasks_completed: int = 0
    tasks_completion_rate_pct: float = 0.0
    alerts_total: int = 0
    alerts_critical: int = 0
    rules_enabled: int = 0
    rules_total: int = 0
    automation_executions: int = 0
    leads_recovered: int = 0
    won_after_automation: int = 0
    average_completion_hours: float = 0.0
    by_priority: dict[str, int] = Field(default_factory=dict)
    by_task_type: dict[str, int] = Field(default_factory=dict)


class BoardColumn(BaseModel):
    key: str
    label: str
    count: int
    tasks: list[AutomationTaskResponse]


class TaskBoardResponse(BaseModel):
    columns: list[BoardColumn]
    total: int


class CalendarEntry(BaseModel):
    task_id: UUID
    title: str
    due_date: datetime
    priority: str
    status: str
    task_type: str
    customer_id: UUID | None
    pipeline_item_id: UUID | None


class CalendarView(BaseModel):
    view: str  # 'day' | 'week' | 'month'
    range_start: datetime
    range_end: datetime
    entries: list[CalendarEntry]
    total: int


__all__ = [
    "AutomationRuleBase",
    "AutomationRuleCreate",
    "AutomationRuleUpdate",
    "AutomationRuleResponse",
    "AutomationTaskBase",
    "AutomationTaskCreate",
    "AutomationTaskUpdate",
    "AutomationTaskResponse",
    "AutomationEventResponse",
    "AutomationMetricsResponse",
    "BoardColumn",
    "TaskBoardResponse",
    "CalendarEntry",
    "CalendarView",
    "TaskStatus",
    "TaskPriority",
    "TaskType",
    "EventSeverity",
    "EntityType",
]
