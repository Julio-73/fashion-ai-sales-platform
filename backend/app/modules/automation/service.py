"""AutomationService — orchestrates rules, tasks, events, metrics, and
the calendar / board projections consumed by the dashboard."""
from __future__ import annotations

import logging
from datetime import datetime, time, timedelta, timezone
from typing import Any, Iterable
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.modules.automation.ai import AutomationAIService
from app.modules.automation.engine import AutomationRuleEngine, EngineStats
from app.modules.automation.models import (
    AutomationEvent,
    AutomationRule,
    AutomationTask,
)
from app.modules.automation.repository import (
    AutomationEventRepository,
    AutomationRuleRepository,
    AutomationTaskRepository,
)
from app.modules.automation.schemas import (
    AutomationEventResponse,
    AutomationMetricsResponse,
    AutomationRuleResponse,
    AutomationTaskResponse,
    BoardColumn,
    CalendarEntry,
    CalendarView,
    TaskBoardResponse,
)

logger = logging.getLogger("ai_sales_agent.automation.service")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _to_task_response(task: AutomationTask) -> AutomationTaskResponse:
    return AutomationTaskResponse.model_validate(task)


def _to_event_response(ev: AutomationEvent) -> AutomationEventResponse:
    return AutomationEventResponse.model_validate(ev)


def _to_rule_response(rule: AutomationRule) -> AutomationRuleResponse:
    return AutomationRuleResponse.model_validate(rule)


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------
class AutomationService:
    """High-level operations. All methods scope by ``empresa_id``."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.rules = AutomationRuleRepository(session)
        self.tasks = AutomationTaskRepository(session)
        self.events = AutomationEventRepository(session)
        self.engine = AutomationRuleEngine(session)
        self.ai = AutomationAIService()

    # ------------------------------------------------------------------
    # Rules
    # ------------------------------------------------------------------
    async def list_rules(
        self, empresa_id: UUID, *, enabled: bool | None = None
    ) -> list[AutomationRuleResponse]:
        rules = await self.rules.list_rules(empresa_id, enabled=enabled)
        return [_to_rule_response(r) for r in rules]

    async def get_rule(self, empresa_id: UUID, rule_id: UUID) -> AutomationRuleResponse:
        rule = await self.rules.get(empresa_id, rule_id)
        if rule is None:
            raise AppError(code="not_found", message="Rule not found", status_code=404)
        return _to_rule_response(rule)

    async def update_rule(
        self, empresa_id: UUID, rule_id: UUID, changes: dict[str, Any]
    ) -> AutomationRuleResponse:
        rule = await self.rules.get(empresa_id, rule_id)
        if rule is None:
            raise AppError(code="not_found", message="Rule not found", status_code=404)
        rule = await self.rules.update(rule=rule, changes=changes)
        await self.session.commit()
        return _to_rule_response(rule)

    async def ensure_seeded(self, empresa_id: UUID) -> list[AutomationRuleResponse]:
        await self.engine.ensure_default_rules(empresa_id)
        await self.session.commit()
        return await self.list_rules(empresa_id)

    # ------------------------------------------------------------------
    # Engine
    # ------------------------------------------------------------------
    async def run_engine(self, empresa_id: UUID) -> EngineStats:
        stats = await self.engine.run(empresa_id)
        logger.info(
            "automation.run empresa=%s scanned_c=%d scanned_d=%d "
            "tasks_created=%d events_created=%d",
            empresa_id,
            stats.scanned_customers,
            stats.scanned_deals,
            stats.tasks_created,
            stats.events_created,
        )
        return stats

    # ------------------------------------------------------------------
    # Tasks
    # ------------------------------------------------------------------
    async def list_tasks(
        self,
        empresa_id: UUID,
        *,
        status: str | None = None,
        priority: str | None = None,
        task_type: str | None = None,
        customer_id: UUID | None = None,
        pipeline_item_id: UUID | None = None,
        rule_id: UUID | None = None,
        search: str | None = None,
        due_before: datetime | None = None,
        due_after: datetime | None = None,
        limit: int = 200,
        offset: int = 0,
    ) -> list[AutomationTaskResponse]:
        tasks = await self.tasks.list_tasks(
            empresa_id=empresa_id,
            status=status,
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
        return [_to_task_response(t) for t in tasks]

    async def get_task(
        self, empresa_id: UUID, task_id: UUID
    ) -> AutomationTaskResponse:
        task = await self.tasks.get(empresa_id, task_id)
        if task is None:
            raise AppError(code="not_found", message="Task not found", status_code=404)
        return _to_task_response(task)

    async def create_task(
        self, empresa_id: UUID, payload: dict[str, Any]
    ) -> AutomationTaskResponse:
        rule_id = payload.get("rule_id")
        task = await self.tasks.create(
            empresa_id=empresa_id,
            rule_id=rule_id,
            customer_id=payload.get("customer_id"),
            pipeline_item_id=payload.get("pipeline_item_id"),
            conversation_id=payload.get("conversation_id"),
            title=payload["title"],
            description=payload.get("description"),
            task_type=payload.get("task_type", "follow_up"),
            priority=payload.get("priority", "medium"),
            status=payload.get("status", "pending"),
            ai_reason=payload.get("ai_reason"),
            ai_next_action=payload.get("ai_next_action"),
            ai_score=payload.get("ai_score"),
            due_date=payload.get("due_date"),
        )
        await self.session.commit()
        return _to_task_response(task)

    async def update_task(
        self, empresa_id: UUID, task_id: UUID, changes: dict[str, Any]
    ) -> AutomationTaskResponse:
        task = await self.tasks.get(empresa_id, task_id)
        if task is None:
            raise AppError(code="not_found", message="Task not found", status_code=404)
        task = await self.tasks.update(task=task, changes=changes)
        await self.session.commit()
        return _to_task_response(task)

    async def complete_task(
        self, empresa_id: UUID, task_id: UUID
    ) -> AutomationTaskResponse:
        return await self.update_task(
            empresa_id, task_id, {"status": "completed"}
        )

    async def cancel_task(
        self, empresa_id: UUID, task_id: UUID
    ) -> AutomationTaskResponse:
        return await self.update_task(
            empresa_id, task_id, {"status": "cancelled"}
        )

    # ------------------------------------------------------------------
    # Board
    # ------------------------------------------------------------------
    async def board(self, empresa_id: UUID) -> TaskBoardResponse:
        now = datetime.now(timezone.utc)
        end_of_day = datetime.combine(now.date(), time.max, tzinfo=timezone.utc)
        end_of_week = now + timedelta(days=7)
        columns: list[BoardColumn] = []

        async def _col(
            key: str,
            label: str,
            tasks: Iterable[AutomationTask],
        ) -> BoardColumn:
            items = list(tasks)
            return BoardColumn(
                key=key,
                label=label,
                count=len(items),
                tasks=[_to_task_response(t) for t in items],
            )

        pending = await self.tasks.list_tasks(
            empresa_id=empresa_id,
            status="pending",
            due_after=end_of_week,
            limit=200,
        )
        today = await self.tasks.list_tasks(
            empresa_id=empresa_id,
            status="pending",
            due_after=now,
            due_before=end_of_day,
            limit=200,
        )
        week = await self.tasks.list_tasks(
            empresa_id=empresa_id,
            status="pending",
            due_after=now,
            due_before=end_of_week,
            limit=200,
        )
        overdue = await self.tasks.list_tasks(
            empresa_id=empresa_id,
            status="overdue",
            limit=200,
        )
        completed = await self.tasks.list_tasks(
            empresa_id=empresa_id,
            status="completed",
            limit=200,
        )

        columns.append(await _col("pendientes", "Pendientes (próximos 7 días)", pending))
        columns.append(await _col("hoy", "Hoy", today))
        columns.append(await _col("semana", "Esta semana", week))
        columns.append(await _col("vencidas", "Vencidas", overdue))
        columns.append(await _col("completadas", "Completadas", completed))

        return TaskBoardResponse(columns=columns, total=sum(c.count for c in columns))

    # ------------------------------------------------------------------
    # Calendar
    # ------------------------------------------------------------------
    async def calendar(
        self,
        empresa_id: UUID,
        *,
        view: str = "week",
        anchor: datetime | None = None,
    ) -> CalendarView:
        anchor = anchor or datetime.now(timezone.utc)
        if view == "day":
            start = datetime.combine(anchor.date(), time.min, tzinfo=timezone.utc)
            end = start + timedelta(days=1)
        elif view == "month":
            start = datetime.combine(
                anchor.date().replace(day=1), time.min, tzinfo=timezone.utc
            )
            # end of month: jump to day 1 of next month
            if start.month == 12:
                end = start.replace(year=start.year + 1, month=1)
            else:
                end = start.replace(month=start.month + 1)
        else:  # week
            start = datetime.combine(
                anchor.date() - timedelta(days=anchor.weekday()),
                time.min,
                tzinfo=timezone.utc,
            )
            end = start + timedelta(days=7)

        rows = await self.tasks.list_for_calendar(
            empresa_id=empresa_id, start=start, end=end
        )
        entries = [
            CalendarEntry(
                task_id=t.id,
                title=t.title,
                due_date=t.due_date,
                priority=t.priority,
                status=t.status,
                task_type=t.task_type,
                customer_id=t.customer_id,
                pipeline_item_id=t.pipeline_item_id,
            )
            for t in rows
            if t.due_date is not None
        ]
        return CalendarView(
            view=view,
            range_start=start,
            range_end=end,
            entries=entries,
            total=len(entries),
        )

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------
    async def list_events(
        self,
        empresa_id: UUID,
        *,
        rule_key: str | None = None,
        entity_type: str | None = None,
        severity: str | None = None,
        limit: int = 100,
    ) -> list[AutomationEventResponse]:
        events = await self.events.list_recent(
            empresa_id=empresa_id,
            rule_key=rule_key,
            entity_type=entity_type,
            severity=severity,
            limit=limit,
        )
        return [_to_event_response(e) for e in events]

    # ------------------------------------------------------------------
    # Metrics
    # ------------------------------------------------------------------
    async def metrics(self, empresa_id: UUID) -> AutomationMetricsResponse:
        now = datetime.now(timezone.utc)
        start_of_day = datetime.combine(now.date(), time.min, tzinfo=timezone.utc)
        end_of_day = start_of_day + timedelta(days=1)
        start_of_week = start_of_day - timedelta(days=now.weekday())
        end_of_week = start_of_week + timedelta(days=7)

        by_status = await self.tasks.count_by_status(empresa_id)
        total_tasks = sum(by_status.values())
        completed_tasks = by_status.get("completed", 0)
        completion_rate = (
            (completed_tasks / total_tasks * 100.0) if total_tasks else 0.0
        )
        by_priority = await self.tasks.count_by_priority(empresa_id)
        by_type = await self.tasks.count_by_task_type(empresa_id)

        overdue = await self.tasks.count_overdue(empresa_id, now)
        today_count = await self.tasks.count_due_between(
            empresa_id, now, end_of_day
        )
        week_count = await self.tasks.count_due_between(
            empresa_id, now, end_of_week
        )
        recovered = await self.tasks.count_completed_recovered(
            empresa_id,
            ("recovery", "follow_up", "call", "proposal", "meeting"),
        )
        won_after = await self.tasks.count_completed_recovered(
            empresa_id, ("proposal", "call", "meeting")
        )
        avg_hours = await self.tasks.average_completion_hours(empresa_id)
        rules_total = await self.rules.count_total(empresa_id)
        rules_enabled = await self.rules.count_enabled(empresa_id)
        exec_total = await self.events.count_total(empresa_id)
        critical_total = await self.events.count_critical(empresa_id)

        return AutomationMetricsResponse(
            tasks_total=total_tasks,
            tasks_pending=by_status.get("pending", 0)
            + by_status.get("overdue", 0)
            + by_status.get("in_progress", 0),
            tasks_today=today_count,
            tasks_this_week=week_count,
            tasks_overdue=overdue,
            tasks_completed=completed_tasks,
            tasks_completion_rate_pct=round(completion_rate, 2),
            alerts_total=exec_total,
            alerts_critical=critical_total,
            rules_enabled=rules_enabled,
            rules_total=rules_total,
            automation_executions=exec_total,
            leads_recovered=recovered,
            won_after_automation=won_after,
            average_completion_hours=round(avg_hours, 2),
            by_priority=by_priority,
            by_task_type=by_type,
        )


__all__ = ["AutomationService"]
