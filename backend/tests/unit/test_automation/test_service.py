"""Unit tests for the AutomationService — service-layer projection
methods (board, calendar, metrics). Uses a mock AsyncSession."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest
import pytest_asyncio

from app.core.errors import AppError
from app.modules.automation.models import (
    AutomationEvent,
    AutomationRule,
    AutomationTask,
)
from app.modules.automation.service import AutomationService


EMPRESA_ID = UUID("11111111-1111-4111-8111-111111111111")


def _task(
    *,
    status: str = "pending",
    priority: str = "medium",
    task_type: str = "follow_up",
    due_date: datetime | None = None,
    title: str = "Tarea de prueba",
) -> AutomationTask:
    t = MagicMock(spec=AutomationTask)
    t.id = uuid4()
    t.empresa_id = EMPRESA_ID
    t.rule_id = None
    t.customer_id = uuid4()
    t.pipeline_item_id = None
    t.conversation_id = None
    t.title = title
    t.description = "d"
    t.task_type = task_type
    t.priority = priority
    t.status = status
    t.ai_reason = None
    t.ai_next_action = None
    t.ai_score = None
    t.due_date = due_date
    t.completed_at = None
    t.created_at = datetime(2026, 6, 1, tzinfo=timezone.utc)
    t.updated_at = datetime(2026, 6, 1, tzinfo=timezone.utc)
    return t


def _build_svc() -> tuple[AutomationService, AsyncMock]:
    session = AsyncMock()
    session.commit = AsyncMock()
    svc = AutomationService(session)
    svc.engine = MagicMock()
    svc.engine.run = AsyncMock(return_value=SimpleNamespace(
        scanned_customers=1, scanned_deals=2, scanned_orders=0, scanned_inventory=0,
        tasks_created=3, tasks_updated=0, events_created=4, rules_skipped=()
    ))
    svc.tasks = MagicMock()
    svc.events = MagicMock()
    svc.rules = MagicMock()
    return svc, session


# ─────────────────────────────────────────────────────────────────────────────
# Rules
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_service_list_rules_passthrough() -> None:
    svc, _ = _build_svc()
    rule = MagicMock(spec=AutomationRule)
    rule.id = uuid4(); rule.empresa_id = EMPRESA_ID; rule.rule_key = "LEAD_NO_RESPONSE_24H"
    rule.name = "Lead sin respuesta 24h"; rule.description = None
    rule.trigger_type = "customer_idle"
    rule.enabled = True; rule.config = {}
    rule.created_at = datetime.now(timezone.utc)
    rule.updated_at = datetime.now(timezone.utc)
    svc.rules.list_rules = AsyncMock(return_value=[rule])
    out = await svc.list_rules(EMPRESA_ID)
    assert out and out[0].rule_key == "LEAD_NO_RESPONSE_24H"


@pytest.mark.asyncio
async def test_service_update_rule_not_found() -> None:
    svc, _ = _build_svc()
    svc.rules.get = AsyncMock(return_value=None)
    with pytest.raises(AppError) as exc:
        await svc.update_rule(EMPRESA_ID, uuid4(), {"enabled": False})
    assert exc.value.code == "not_found"


@pytest.mark.asyncio
async def test_service_update_rule_ok() -> None:
    svc, _ = _build_svc()
    rule = MagicMock(spec=AutomationRule)
    rule.id = uuid4(); rule.empresa_id = EMPRESA_ID; rule.rule_key = "LEAD_NO_RESPONSE_24H"
    rule.name = "Lead sin respuesta 24h"; rule.description = None
    rule.trigger_type = "customer_idle"
    rule.enabled = True; rule.config = {}
    rule.created_at = datetime.now(timezone.utc)
    rule.updated_at = datetime.now(timezone.utc)
    svc.rules.get = AsyncMock(return_value=rule)
    svc.rules.update = AsyncMock(return_value=rule)
    out = await svc.update_rule(EMPRESA_ID, rule.id, {"enabled": False})
    assert out.id == rule.id


@pytest.mark.asyncio
async def test_service_ensure_seeded_invokes_engine() -> None:
    svc, _ = _build_svc()
    svc.engine.ensure_default_rules = AsyncMock(return_value=[])
    rule = MagicMock(spec=AutomationRule)
    rule.id = uuid4(); rule.empresa_id = EMPRESA_ID; rule.rule_key = "LEAD_NO_RESPONSE_24H"
    rule.name = "Lead sin respuesta 24h"; rule.description = None
    rule.trigger_type = "customer_idle"
    rule.enabled = True; rule.config = {}
    rule.created_at = datetime.now(timezone.utc)
    rule.updated_at = datetime.now(timezone.utc)
    svc.rules.list_rules = AsyncMock(return_value=[rule])
    out = await svc.ensure_seeded(EMPRESA_ID)
    assert out and out[0].rule_key == "LEAD_NO_RESPONSE_24H"


# ─────────────────────────────────────────────────────────────────────────────
# Tasks
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_service_get_task_not_found() -> None:
    svc, _ = _build_svc()
    svc.tasks.get = AsyncMock(return_value=None)
    with pytest.raises(AppError) as exc:
        await svc.get_task(EMPRESA_ID, uuid4())
    assert exc.value.code == "not_found"


@pytest.mark.asyncio
async def test_service_create_task_passthrough() -> None:
    svc, _ = _build_svc()
    svc.tasks.create = AsyncMock(side_effect=lambda **kw: MagicMock(
        id=uuid4(), empresa_id=EMPRESA_ID, rule_id=None, customer_id=None,
        pipeline_item_id=None, conversation_id=None, title=kw["title"],
        description=kw["description"], task_type=kw["task_type"],
        priority=kw["priority"], status=kw["status"],
        ai_reason=None, ai_next_action=None, ai_score=None,
        due_date=kw["due_date"], completed_at=None,
        created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc),
    ))
    out = await svc.create_task(EMPRESA_ID, {
        "title": "Llamar al cliente",
        "description": "x",
        "task_type": "call",
        "priority": "high",
    })
    assert out.title == "Llamar al cliente"


@pytest.mark.asyncio
async def test_service_complete_task_marks_completed() -> None:
    svc, _ = _build_svc()
    task = _task()
    svc.tasks.get = AsyncMock(return_value=task)
    svc.tasks.update = AsyncMock(return_value=task)
    await svc.complete_task(EMPRESA_ID, task.id)
    svc.tasks.update.assert_awaited()


@pytest.mark.asyncio
async def test_service_cancel_task_marks_cancelled() -> None:
    svc, _ = _build_svc()
    task = _task()
    svc.tasks.get = AsyncMock(return_value=task)
    svc.tasks.update = AsyncMock(return_value=task)
    await svc.cancel_task(EMPRESA_ID, task.id)
    svc.tasks.update.assert_awaited()


# ─────────────────────────────────────────────────────────────────────────────
# Board projection
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_service_board_groups_in_columns() -> None:
    svc, _ = _build_svc()
    now = datetime.now(timezone.utc)
    pending = _task(status="pending", due_date=now + timedelta(days=2))
    today = _task(status="pending", due_date=now + timedelta(hours=4))
    overdue = _task(status="overdue", due_date=now - timedelta(days=1))
    completed = _task(status="completed", due_date=None)

    svc.tasks.list_tasks = AsyncMock(side_effect=[
        [pending],        # pendientes
        [today],          # hoy
        [today, pending], # semana
        [overdue],        # vencidas
        [completed],      # completadas
    ])
    board = await svc.board(EMPRESA_ID)
    keys = [c.key for c in board.columns]
    assert keys == ["pendientes", "hoy", "semana", "vencidas", "completadas"]
    assert board.total >= 1


# ─────────────────────────────────────────────────────────────────────────────
# Calendar projection
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_service_calendar_view_week() -> None:
    svc, _ = _build_svc()
    task = _task(due_date=datetime(2026, 6, 8, 10, 0, tzinfo=timezone.utc))
    svc.tasks.list_for_calendar = AsyncMock(return_value=[task])
    view = await svc.calendar(EMPRESA_ID, view="week")
    assert view.view == "week"
    assert view.total == 1
    assert view.entries[0].title == "Tarea de prueba"


@pytest.mark.asyncio
async def test_service_calendar_view_day() -> None:
    svc, _ = _build_svc()
    svc.tasks.list_for_calendar = AsyncMock(return_value=[])
    view = await svc.calendar(EMPRESA_ID, view="day")
    assert view.view == "day"


@pytest.mark.asyncio
async def test_service_calendar_view_month() -> None:
    svc, _ = _build_svc()
    svc.tasks.list_for_calendar = AsyncMock(return_value=[])
    view = await svc.calendar(EMPRESA_ID, view="month")
    assert view.view == "month"


# ─────────────────────────────────────────────────────────────────────────────
# Metrics
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_service_metrics_aggregates() -> None:
    svc, _ = _build_svc()
    svc.tasks.count_by_status = AsyncMock(return_value={
        "pending": 5, "completed": 3, "overdue": 1, "in_progress": 1
    })
    svc.tasks.count_by_priority = AsyncMock(return_value={"high": 2, "low": 8})
    svc.tasks.count_by_task_type = AsyncMock(return_value={"follow_up": 7, "alert": 2})
    svc.tasks.count_overdue = AsyncMock(return_value=1)
    svc.tasks.count_due_between = AsyncMock(side_effect=[3, 10])
    svc.tasks.count_completed_between = AsyncMock(side_effect=[2, 5])
    svc.tasks.count_completed_recovered = AsyncMock(side_effect=[2, 1])
    svc.tasks.average_completion_hours = AsyncMock(return_value=4.5)
    svc.rules.count_total = AsyncMock(return_value=7)
    svc.rules.count_enabled = AsyncMock(return_value=6)
    svc.events.count_total = AsyncMock(return_value=12)
    svc.events.count_critical = AsyncMock(return_value=2)

    m = await svc.metrics(EMPRESA_ID)
    assert m.tasks_total == 10
    assert m.tasks_pending == 7
    assert m.tasks_completed == 3
    assert m.tasks_overdue == 1
    assert m.tasks_today == 3
    assert m.tasks_this_week == 10
    assert m.alerts_total == 12
    assert m.alerts_critical == 2
    assert m.rules_total == 7
    assert m.rules_enabled == 6
    assert m.leads_recovered == 2
    assert m.won_after_automation == 1
    assert m.average_completion_hours == 4.5
    assert m.by_priority == {"high": 2, "low": 8}
    assert m.by_task_type == {"follow_up": 7, "alert": 2}


@pytest.mark.asyncio
async def test_service_metrics_handles_empty_tenant() -> None:
    svc, _ = _build_svc()
    svc.tasks.count_by_status = AsyncMock(return_value={})
    svc.tasks.count_by_priority = AsyncMock(return_value={})
    svc.tasks.count_by_task_type = AsyncMock(return_value={})
    svc.tasks.count_overdue = AsyncMock(return_value=0)
    svc.tasks.count_due_between = AsyncMock(side_effect=[0, 0])
    svc.tasks.count_completed_between = AsyncMock(side_effect=[0, 0])
    svc.tasks.count_completed_recovered = AsyncMock(side_effect=[0, 0])
    svc.tasks.average_completion_hours = AsyncMock(return_value=0.0)
    svc.rules.count_total = AsyncMock(return_value=0)
    svc.rules.count_enabled = AsyncMock(return_value=0)
    svc.events.count_total = AsyncMock(return_value=0)
    svc.events.count_critical = AsyncMock(return_value=0)

    m = await svc.metrics(EMPRESA_ID)
    assert m.tasks_total == 0
    assert m.tasks_completion_rate_pct == 0.0
    assert m.alerts_total == 0


# ─────────────────────────────────────────────────────────────────────────────
# Engine
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_service_run_engine_passthrough() -> None:
    svc, _ = _build_svc()
    stats = await svc.run_engine(EMPRESA_ID)
    assert stats.tasks_created == 3
    assert stats.events_created == 4


# ─────────────────────────────────────────────────────────────────────────────
# Events
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_service_list_events_passthrough() -> None:
    svc, _ = _build_svc()
    ev = MagicMock(spec=AutomationEvent)
    ev.id = uuid4(); ev.empresa_id = EMPRESA_ID
    ev.rule_id = None; ev.rule_key = "RULE_001"
    ev.event_type = "lead_idle"
    ev.entity_type = "customer"
    ev.entity_id = uuid4()
    ev.severity = "warning"
    ev.payload = {}
    ev.created_at = datetime.now(timezone.utc)
    svc.events.list_recent = AsyncMock(return_value=[ev])
    out = await svc.list_events(EMPRESA_ID, severity="warning")
    assert out and out[0].rule_key == "RULE_001"


# ─────────────────────────────────────────────────────────────────────────────
# Tasks list
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_service_list_tasks_passthrough() -> None:
    svc, _ = _build_svc()
    task = _task()
    svc.tasks.list_tasks = AsyncMock(return_value=[task])
    out = await svc.list_tasks(EMPRESA_ID, status="pending")
    assert len(out) == 1
    svc.tasks.list_tasks.assert_awaited()
