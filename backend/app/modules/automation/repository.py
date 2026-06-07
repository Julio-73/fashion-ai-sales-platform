"""Repository — pure data access for automation tables.

No business rules. No tenant enforcement at the SQL level (the
service layer scopes by ``empresa_id``). The repository never raises
business errors; it returns ``None`` / empty lists for missing rows.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Sequence
from uuid import UUID

from sqlalchemy import and_, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.automation.models import (
    AutomationEvent,
    AutomationRule,
    AutomationTask,
)


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------
class AutomationRuleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_rules(
        self, empresa_id: UUID, *, enabled: bool | None = None
    ) -> Sequence[AutomationRule]:
        stmt = select(AutomationRule).where(
            AutomationRule.empresa_id == empresa_id
        )
        if enabled is not None:
            stmt = stmt.where(AutomationRule.enabled.is_(enabled))
        stmt = stmt.order_by(AutomationRule.rule_key)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_key(
        self, empresa_id: UUID, rule_key: str
    ) -> AutomationRule | None:
        stmt = select(AutomationRule).where(
            and_(
                AutomationRule.empresa_id == empresa_id,
                AutomationRule.rule_key == rule_key,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get(self, empresa_id: UUID, rule_id: UUID) -> AutomationRule | None:
        stmt = select(AutomationRule).where(
            and_(
                AutomationRule.empresa_id == empresa_id,
                AutomationRule.id == rule_id,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def upsert_seed(
        self,
        *,
        empresa_id: UUID,
        rule_key: str,
        name: str,
        description: str | None,
        trigger_type: str,
        default_config: dict[str, Any] | None = None,
    ) -> AutomationRule:
        existing = await self.get_by_key(empresa_id, rule_key)
        if existing is not None:
            return existing
        rule = AutomationRule(
            empresa_id=empresa_id,
            rule_key=rule_key,
            name=name,
            description=description,
            trigger_type=trigger_type,
            enabled=True,
            config=default_config or {},
        )
        self.session.add(rule)
        await self.session.flush()
        return rule

    async def create(
        self,
        *,
        empresa_id: UUID,
        rule_key: str,
        name: str,
        description: str | None,
        trigger_type: str,
        enabled: bool,
        config: dict[str, Any],
    ) -> AutomationRule:
        rule = AutomationRule(
            empresa_id=empresa_id,
            rule_key=rule_key,
            name=name,
            description=description,
            trigger_type=trigger_type,
            enabled=enabled,
            config=config,
        )
        self.session.add(rule)
        await self.session.flush()
        return rule

    async def update(
        self, *, rule: AutomationRule, changes: dict[str, Any]
    ) -> AutomationRule:
        for k, v in changes.items():
            if v is None and k in {"description", "config"}:
                continue
            setattr(rule, k, v)
        await self.session.flush()
        return rule

    async def count_enabled(self, empresa_id: UUID) -> int:
        stmt = select(func.count(AutomationRule.id)).where(
            and_(
                AutomationRule.empresa_id == empresa_id,
                AutomationRule.enabled.is_(True),
            )
        )
        return int((await self.session.execute(stmt)).scalar() or 0)

    async def count_total(self, empresa_id: UUID) -> int:
        stmt = select(func.count(AutomationRule.id)).where(
            AutomationRule.empresa_id == empresa_id
        )
        return int((await self.session.execute(stmt)).scalar() or 0)


# ---------------------------------------------------------------------------
# Tasks
# ---------------------------------------------------------------------------
class AutomationTaskRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_tasks(
        self,
        *,
        empresa_id: UUID,
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
    ) -> Sequence[AutomationTask]:
        stmt = select(AutomationTask).where(
            AutomationTask.empresa_id == empresa_id
        )
        if status is not None:
            stmt = stmt.where(AutomationTask.status == status)
        if priority is not None:
            stmt = stmt.where(AutomationTask.priority == priority)
        if task_type is not None:
            stmt = stmt.where(AutomationTask.task_type == task_type)
        if customer_id is not None:
            stmt = stmt.where(AutomationTask.customer_id == customer_id)
        if pipeline_item_id is not None:
            stmt = stmt.where(AutomationTask.pipeline_item_id == pipeline_item_id)
        if rule_id is not None:
            stmt = stmt.where(AutomationTask.rule_id == rule_id)
        if due_before is not None:
            stmt = stmt.where(AutomationTask.due_date <= due_before)
        if due_after is not None:
            stmt = stmt.where(AutomationTask.due_date >= due_after)
        if search:
            like = f"%{search.lower()}%"
            stmt = stmt.where(func.lower(AutomationTask.title).like(like))
        stmt = (
            stmt.order_by(
                AutomationTask.due_date.is_(None),
                AutomationTask.due_date.asc(),
                AutomationTask.created_at.desc(),
            )
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get(self, empresa_id: UUID, task_id: UUID) -> AutomationTask | None:
        stmt = select(AutomationTask).where(
            and_(
                AutomationTask.empresa_id == empresa_id,
                AutomationTask.id == task_id,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(
        self,
        *,
        empresa_id: UUID,
        rule_id: UUID | None,
        customer_id: UUID | None,
        pipeline_item_id: UUID | None,
        conversation_id: UUID | None,
        title: str,
        description: str | None,
        task_type: str,
        priority: str,
        status: str,
        ai_reason: str | None,
        ai_next_action: str | None,
        ai_score: int | None,
        due_date: datetime | None,
    ) -> AutomationTask:
        task = AutomationTask(
            empresa_id=empresa_id,
            rule_id=rule_id,
            customer_id=customer_id,
            pipeline_item_id=pipeline_item_id,
            conversation_id=conversation_id,
            title=title,
            description=description,
            task_type=task_type,
            priority=priority,
            status=status,
            ai_reason=ai_reason,
            ai_next_action=ai_next_action,
            ai_score=ai_score,
            due_date=due_date,
        )
        self.session.add(task)
        await self.session.flush()
        return task

    async def update(
        self, *, task: AutomationTask, changes: dict[str, Any]
    ) -> AutomationTask:
        for k, v in changes.items():
            setattr(task, k, v)
        if (
            changes.get("status") == "completed"
            and task.completed_at is None
        ):
            task.completed_at = datetime.utcnow()
        await self.session.flush()
        return task

    async def find_open_duplicate(
        self,
        *,
        empresa_id: UUID,
        rule_id: UUID | None,
        customer_id: UUID | None,
        pipeline_item_id: UUID | None,
        title: str,
    ) -> AutomationTask | None:
        """Return an existing non-terminal task for the same logical
        trigger. Used to avoid spamming the task center when the
        engine re-runs every cycle."""
        stmt = select(AutomationTask).where(
            and_(
                AutomationTask.empresa_id == empresa_id,
                AutomationTask.title == title,
                AutomationTask.status.in_(
                    ("pending", "in_progress", "overdue")
                ),
            )
        )
        if rule_id is not None:
            stmt = stmt.where(AutomationTask.rule_id == rule_id)
        if customer_id is not None:
            stmt = stmt.where(AutomationTask.customer_id == customer_id)
        if pipeline_item_id is not None:
            stmt = stmt.where(
                AutomationTask.pipeline_item_id == pipeline_item_id
            )
        stmt = stmt.order_by(AutomationTask.created_at.desc()).limit(1)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def count_by_status(self, empresa_id: UUID) -> dict[str, int]:
        stmt = select(AutomationTask.status, func.count(AutomationTask.id)).where(
            AutomationTask.empresa_id == empresa_id
        ).group_by(AutomationTask.status)
        result = await self.session.execute(stmt)
        return {s: int(c) for s, c in result.all()}

    async def count_by_priority(self, empresa_id: UUID) -> dict[str, int]:
        stmt = select(AutomationTask.priority, func.count(AutomationTask.id)).where(
            AutomationTask.empresa_id == empresa_id
        ).group_by(AutomationTask.priority)
        result = await self.session.execute(stmt)
        return {p: int(c) for p, c in result.all()}

    async def count_by_task_type(self, empresa_id: UUID) -> dict[str, int]:
        stmt = select(AutomationTask.task_type, func.count(AutomationTask.id)).where(
            AutomationTask.empresa_id == empresa_id
        ).group_by(AutomationTask.task_type)
        result = await self.session.execute(stmt)
        return {t: int(c) for t, c in result.all()}

    async def count_overdue(self, empresa_id: UUID, now: datetime) -> int:
        stmt = select(func.count(AutomationTask.id)).where(
            and_(
                AutomationTask.empresa_id == empresa_id,
                AutomationTask.status.in_(("pending", "in_progress", "overdue")),
                AutomationTask.due_date.is_not(None),
                AutomationTask.due_date < now,
            )
        )
        return int((await self.session.execute(stmt)).scalar() or 0)

    async def count_due_between(
        self, empresa_id: UUID, start: datetime, end: datetime
    ) -> int:
        stmt = select(func.count(AutomationTask.id)).where(
            and_(
                AutomationTask.empresa_id == empresa_id,
                AutomationTask.due_date.is_not(None),
                AutomationTask.due_date >= start,
                AutomationTask.due_date < end,
                AutomationTask.status.in_(("pending", "in_progress", "overdue")),
            )
        )
        return int((await self.session.execute(stmt)).scalar() or 0)

    async def count_completed_between(
        self, empresa_id: UUID, start: datetime, end: datetime
    ) -> int:
        stmt = select(func.count(AutomationTask.id)).where(
            and_(
                AutomationTask.empresa_id == empresa_id,
                AutomationTask.status == "completed",
                AutomationTask.completed_at.is_not(None),
                AutomationTask.completed_at >= start,
                AutomationTask.completed_at < end,
            )
        )
        return int((await self.session.execute(stmt)).scalar() or 0)

    async def count_completed_recovered(
        self, empresa_id: UUID, task_types: tuple[str, ...]
    ) -> int:
        stmt = select(func.count(AutomationTask.id)).where(
            and_(
                AutomationTask.empresa_id == empresa_id,
                AutomationTask.status == "completed",
                AutomationTask.task_type.in_(task_types),
            )
        )
        return int((await self.session.execute(stmt)).scalar() or 0)

    async def count_completed_total(self, empresa_id: UUID) -> int:
        stmt = select(func.count(AutomationTask.id)).where(
            and_(
                AutomationTask.empresa_id == empresa_id,
                AutomationTask.status == "completed",
            )
        )
        return int((await self.session.execute(stmt)).scalar() or 0)

    async def average_completion_hours(self, empresa_id: UUID) -> float:
        """Average hours between creation and completion for closed tasks."""
        hours_expr = func.extract(
            "epoch",
            AutomationTask.completed_at - AutomationTask.created_at,
        ) / 3600.0
        stmt = select(func.coalesce(func.avg(hours_expr), 0)).where(
            and_(
                AutomationTask.empresa_id == empresa_id,
                AutomationTask.status == "completed",
                AutomationTask.completed_at.is_not(None),
            )
        )
        return float((await self.session.execute(stmt)).scalar() or 0)

    async def list_for_calendar(
        self,
        *,
        empresa_id: UUID,
        start: datetime,
        end: datetime,
    ) -> Sequence[AutomationTask]:
        stmt = (
            select(AutomationTask)
            .where(
                and_(
                    AutomationTask.empresa_id == empresa_id,
                    AutomationTask.due_date.is_not(None),
                    AutomationTask.due_date >= start,
                    AutomationTask.due_date < end,
                )
            )
            .order_by(AutomationTask.due_date.asc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def mark_overdue(self, empresa_id: UUID, now: datetime) -> int:
        """Flip ``pending``/``in_progress`` tasks whose ``due_date`` is
        in the past to ``overdue``. Returns the affected row count."""
        stmt = (
            update(AutomationTask)
            .where(
                and_(
                    AutomationTask.empresa_id == empresa_id,
                    AutomationTask.status.in_(("pending", "in_progress")),
                    AutomationTask.due_date.is_not(None),
                    AutomationTask.due_date < now,
                )
            )
            .values(status="overdue")
        )
        result = await self.session.execute(stmt)
        return int(result.rowcount or 0)


# ---------------------------------------------------------------------------
# Events
# ---------------------------------------------------------------------------
class AutomationEventRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        *,
        empresa_id: UUID,
        rule_id: UUID | None,
        rule_key: str,
        event_type: str,
        entity_type: str,
        entity_id: UUID | None,
        severity: str,
        payload: dict[str, Any],
    ) -> AutomationEvent:
        ev = AutomationEvent(
            empresa_id=empresa_id,
            rule_id=rule_id,
            rule_key=rule_key,
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            severity=severity,
            payload=payload,
        )
        self.session.add(ev)
        await self.session.flush()
        return ev

    async def list_recent(
        self,
        *,
        empresa_id: UUID,
        rule_key: str | None = None,
        entity_type: str | None = None,
        severity: str | None = None,
        limit: int = 100,
    ) -> Sequence[AutomationEvent]:
        stmt = select(AutomationEvent).where(
            AutomationEvent.empresa_id == empresa_id
        )
        if rule_key is not None:
            stmt = stmt.where(AutomationEvent.rule_key == rule_key)
        if entity_type is not None:
            stmt = stmt.where(AutomationEvent.entity_type == entity_type)
        if severity is not None:
            stmt = stmt.where(AutomationEvent.severity == severity)
        stmt = stmt.order_by(AutomationEvent.created_at.desc()).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def count_total(self, empresa_id: UUID) -> int:
        stmt = select(func.count(AutomationEvent.id)).where(
            AutomationEvent.empresa_id == empresa_id
        )
        return int((await self.session.execute(stmt)).scalar() or 0)

    async def count_between(
        self, empresa_id: UUID, start: datetime, end: datetime
    ) -> int:
        stmt = select(func.count(AutomationEvent.id)).where(
            and_(
                AutomationEvent.empresa_id == empresa_id,
                AutomationEvent.created_at >= start,
                AutomationEvent.created_at < end,
            )
        )
        return int((await self.session.execute(stmt)).scalar() or 0)

    async def count_critical(self, empresa_id: UUID) -> int:
        stmt = select(func.count(AutomationEvent.id)).where(
            and_(
                AutomationEvent.empresa_id == empresa_id,
                AutomationEvent.severity == "critical",
            )
        )
        return int((await self.session.execute(stmt)).scalar() or 0)


__all__ = [
    "AutomationRuleRepository",
    "AutomationTaskRepository",
    "AutomationEventRepository",
]
