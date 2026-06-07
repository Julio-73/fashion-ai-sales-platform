"""Automation rule engine.

Pure orchestration. Receives an ``AsyncSession`` and a tenant id, scans
the relevant frozen tables (read-only), and emits:
    * ``automation_tasks``  — actionable items
    * ``automation_events`` — audit log entries

The engine never writes to any frozen module's tables.

Idempotency: ``AutomationTaskRepository.find_open_duplicate`` is used
to avoid creating multiple open tasks for the same logical trigger.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Iterable
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.conversations.models import MessageCore
from app.modules.automation.ai import AutomationAIService
from app.modules.automation.models import (
    DEFAULT_RULES,
    RULE_001,
    RULE_002,
    RULE_003,
    RULE_004,
    RULE_005,
    RULE_006,
    RULE_007,
    AutomationEvent,
    AutomationRule,
    AutomationTask,
)
from app.modules.automation.repository import (
    AutomationEventRepository,
    AutomationRuleRepository,
    AutomationTaskRepository,
)
from app.modules.customers.models import Cliente
from app.modules.pipeline.models import (
    LOST_STAGE,
    NEW_LEAD_STAGE,
    OPEN_STAGES,
    WON_STAGE,
    SalesPipelineItem,
)
from app.modules.whatsapp.models import WhatsappMessage

logger = logging.getLogger("ai_sales_agent.automation")


# ---------------------------------------------------------------------------
# Thresholds — read by the engine and the AI service
# ---------------------------------------------------------------------------
LEAD_IDLE_24H_HOURS = 24
LEAD_IDLE_48H_HOURS = 48
NEGOTIATION_STUCK_DAYS = 7
VIP_INACTIVE_DAYS = 30
HIGH_VALUE_THRESHOLD = Decimal("2000")
INVENTORY_LOW_THRESHOLD = 5


# ---------------------------------------------------------------------------
# Engine stats — returned to the caller for observability
# ---------------------------------------------------------------------------
@dataclass
class EngineStats:
    scanned_customers: int = 0
    scanned_deals: int = 0
    scanned_orders: int = 0
    scanned_inventory: int = 0
    tasks_created: int = 0
    tasks_updated: int = 0
    events_created: int = 0
    rules_skipped: tuple[str, ...] = ()


# ---------------------------------------------------------------------------
# Rule engine
# ---------------------------------------------------------------------------
class AutomationRuleEngine:
    """Read-only scan + write side-effects to automation tables only."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.rules = AutomationRuleRepository(session)
        self.tasks = AutomationTaskRepository(session)
        self.events = AutomationEventRepository(session)
        self.ai = AutomationAIService()

    # ------------------------------------------------------------------
    # Seeding — called once per tenant on first use
    # ------------------------------------------------------------------
    async def ensure_default_rules(self, empresa_id: UUID) -> list[AutomationRule]:
        seeded: list[AutomationRule] = []
        for spec in DEFAULT_RULES:
            rule = await self.rules.upsert_seed(
                empresa_id=empresa_id,
                rule_key=spec["rule_key"],
                name=spec["name"],
                description=spec["description"],
                trigger_type=spec["trigger_type"],
                default_config={},
            )
            seeded.append(rule)
        return seeded

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------
    async def run(self, empresa_id: UUID, *, now: datetime | None = None) -> EngineStats:
        now = now or datetime.now(timezone.utc)
        stats = EngineStats()
        rules = await self.rules.list_rules(empresa_id, enabled=True)
        rules_by_key = {r.rule_key: r for r in rules}

        # 1) Mark stale tasks as overdue
        try:
            await self.tasks.mark_overdue(empresa_id, now)
        except Exception:  # pragma: no cover - robustness
            logger.exception("mark_overdue failed")

        # 2) Run every rule. Each method is isolated so a failure in
        #    one does not affect the others.
        for rule_key, runner in (
            (RULE_001, self._rule_lead_no_response_24h),
            (RULE_002, self._rule_lead_no_response_48h),
            (RULE_003, self._rule_negotiation_stuck_7d),
            (RULE_004, self._rule_vip_inactive_30d),
            (RULE_005, self._rule_new_high_value_lead),
            (RULE_006, self._rule_pipeline_won),
            (RULE_007, self._rule_pipeline_lost),
        ):
            if rule_key not in rules_by_key:
                stats.rules_skipped = stats.rules_skipped + (rule_key,)
                continue
            rule = rules_by_key[rule_key]
            try:
                await runner(empresa_id, rule, now, stats)
            except Exception:
                logger.exception("rule %s failed", rule_key)

        await self.session.commit()
        return stats

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _priority_from(self, rule: AutomationRule, fallback: str) -> str:
        return (rule.config or {}).get("priority", fallback) or fallback

    def _severity_from(self, rule: AutomationRule, fallback: str) -> str:
        return (rule.config or {}).get("severity", fallback) or fallback

    def _due_in(self, hours: int, now: datetime) -> datetime:
        return now + timedelta(hours=hours)

    async def _customer_map(
        self, ids: Iterable[UUID | None]
    ) -> dict[UUID, Cliente]:
        clean = [i for i in ids if i is not None]
        if not clean:
            return {}
        stmt = select(Cliente).where(Cliente.id.in_(clean))
        return {c.id: c for c in (await self.session.execute(stmt)).scalars()}

    async def _last_inbound_whatsapp(
        self, empresa_id: UUID, customer_ids: list[UUID]
    ) -> dict[UUID, datetime]:
        if not customer_ids:
            return {}
        # We don't have a customer_id FK on whatsapp_messages (only on
        # conversations). Approximate via conversations->customer.
        from app.modules.conversations.models import ConversationCore  # local import

        stmt = (
            select(
                ConversationCore.customer_id,
                func.max(WhatsappMessage.created_at),
            )
            .join(
                WhatsappMessage,
                WhatsappMessage.conversation_id == ConversationCore.id,
            )
            .where(
                and_(
                    ConversationCore.empresa_id == empresa_id,
                    ConversationCore.customer_id.in_(customer_ids),
                    WhatsappMessage.direction == "inbound",
                )
            )
            .group_by(ConversationCore.customer_id)
        )
        rows = (await self.session.execute(stmt)).all()
        return {cid: ts for cid, ts in rows if ts is not None}

    async def _last_message_core(
        self, customer_ids: list[UUID]
    ) -> dict[UUID, datetime]:
        if not customer_ids:
            return {}
        from app.modules.conversations.models import ConversationCore  # local

        stmt = (
            select(
                ConversationCore.customer_id,
                func.max(MessageCore.created_at),
            )
            .join(
                MessageCore,
                MessageCore.conversation_id == ConversationCore.id,
            )
            .where(ConversationCore.customer_id.in_(customer_ids))
            .group_by(ConversationCore.customer_id)
        )
        rows = (await self.session.execute(stmt)).all()
        return {cid: ts for cid, ts in rows if ts is not None}

    # ------------------------------------------------------------------
    # Side-effect writers
    # ------------------------------------------------------------------
    async def _create_task(
        self,
        *,
        empresa_id: UUID,
        rule: AutomationRule,
        title: str,
        description: str,
        task_type: str,
        priority: str,
        due_date: datetime | None,
        customer_id: UUID | None,
        pipeline_item_id: UUID | None,
        conversation_id: UUID | None,
        ai_reason: str,
        ai_next_action: str,
        ai_score: int,
        stats: EngineStats,
    ) -> AutomationTask | None:
        existing = await self.tasks.find_open_duplicate(
            empresa_id=empresa_id,
            rule_id=rule.id,
            customer_id=customer_id,
            pipeline_item_id=pipeline_item_id,
            title=title,
        )
        if existing is not None:
            # Refresh priority if the AI bumped it up
            if priority == "critical" and existing.priority != "critical":
                existing.priority = "critical"
                stats.tasks_updated += 1
            return existing
        task = await self.tasks.create(
            empresa_id=empresa_id,
            rule_id=rule.id,
            customer_id=customer_id,
            pipeline_item_id=pipeline_item_id,
            conversation_id=conversation_id,
            title=title,
            description=description,
            task_type=task_type,
            priority=priority,
            status="pending",
            ai_reason=ai_reason,
            ai_next_action=ai_next_action,
            ai_score=ai_score,
            due_date=due_date,
        )
        stats.tasks_created += 1
        return task

    async def _create_event(
        self,
        *,
        empresa_id: UUID,
        rule: AutomationRule,
        event_type: str,
        entity_type: str,
        entity_id: UUID | None,
        severity: str,
        payload: dict[str, Any],
        stats: EngineStats,
    ) -> AutomationEvent:
        ev = await self.events.create(
            empresa_id=empresa_id,
            rule_id=rule.id,
            rule_key=rule.rule_key,
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            severity=severity,
            payload=payload,
        )
        stats.events_created += 1
        return ev

    # ------------------------------------------------------------------
    # RULE 001 — LEAD_NO_RESPONSE_24H
    # ------------------------------------------------------------------
    async def _rule_lead_no_response_24h(
        self,
        empresa_id: UUID,
        rule: AutomationRule,
        now: datetime,
        stats: EngineStats,
    ) -> None:
        idle_after = now - timedelta(hours=LEAD_IDLE_24H_HOURS)
        stmt = (
            select(Cliente)
            .where(
                and_(
                    Cliente.empresa_id == empresa_id,
                    Cliente.deleted_at.is_(None),
                    Cliente.lead_status.in_(("new", "interested")),
                    Cliente.last_interaction_at.is_not(None),
                    Cliente.last_interaction_at < idle_after,
                )
            )
            .limit(500)
        )
        customers = list((await self.session.execute(stmt)).scalars())
        stats.scanned_customers += len(customers)
        if not customers:
            return
        for c in customers:
            idle_h = int((now - c.last_interaction_at).total_seconds() // 3600)
            if idle_h < LEAD_IDLE_24H_HOURS:
                continue
            ai_prio, ai_reason, ai_action, ai_score = self.ai.recommend(
                RULE_001,
                customer=c,
                deal=None,
            )
            priority = self._priority_from(rule, ai_prio)
            await self._create_task(
                empresa_id=empresa_id,
                rule=rule,
                title=f"Follow-up: {c.full_name}",
                description=(
                    f"Cliente {c.full_name} sin respuesta hace "
                    f"{idle_h} h. Reactivar por WhatsApp."
                ),
                task_type="follow_up",
                priority=priority,
                due_date=self._due_in(4, now),
                customer_id=c.id,
                pipeline_item_id=None,
                conversation_id=c.last_conversation_id,
                ai_reason=ai_reason,
                ai_next_action=ai_action,
                ai_score=ai_score,
                stats=stats,
            )
            if idle_h >= LEAD_IDLE_48H_HOURS:
                # Skip — RULE_002 owns the 48h+ escalation
                continue

    # ------------------------------------------------------------------
    # RULE 002 — LEAD_NO_RESPONSE_48H
    # ------------------------------------------------------------------
    async def _rule_lead_no_response_48h(
        self,
        empresa_id: UUID,
        rule: AutomationRule,
        now: datetime,
        stats: EngineStats,
    ) -> None:
        idle_after = now - timedelta(hours=LEAD_IDLE_48H_HOURS)
        stmt = (
            select(Cliente)
            .where(
                and_(
                    Cliente.empresa_id == empresa_id,
                    Cliente.deleted_at.is_(None),
                    Cliente.lead_status.in_(("new", "interested", "negotiating")),
                    Cliente.last_interaction_at.is_not(None),
                    Cliente.last_interaction_at < idle_after,
                )
            )
            .limit(500)
        )
        customers = list((await self.session.execute(stmt)).scalars())
        stats.scanned_customers += len(customers)
        for c in customers:
            idle_h = int((now - c.last_interaction_at).total_seconds() // 3600)
            if idle_h < LEAD_IDLE_48H_HOURS:
                continue
            ai_prio, ai_reason, ai_action, ai_score = self.ai.recommend(
                RULE_002,
                customer=c,
                deal=None,
            )
            priority = self._priority_from(rule, ai_prio)
            title = f"CRÍTICO: contactar a {c.full_name}"
            task = await self._create_task(
                empresa_id=empresa_id,
                rule=rule,
                title=title,
                description=(
                    f"Lead en silencio {idle_h} h — asignar y llamar HOY."
                ),
                task_type="alert",
                priority=priority,
                due_date=self._due_in(2, now),
                customer_id=c.id,
                pipeline_item_id=None,
                conversation_id=c.last_conversation_id,
                ai_reason=ai_reason,
                ai_next_action=ai_action,
                ai_score=ai_score,
                stats=stats,
            )
            await self._create_event(
                empresa_id=empresa_id,
                rule=rule,
                event_type="lead_idle_48h",
                entity_type="customer",
                entity_id=c.id,
                severity=self._severity_from(rule, "critical"),
                payload={
                    "customer_id": str(c.id),
                    "full_name": c.full_name,
                    "idle_hours": idle_h,
                    "task_id": str(task.id) if task else None,
                },
                stats=stats,
            )

    # ------------------------------------------------------------------
    # RULE 003 — NEGOTIATION_STUCK_7D
    # ------------------------------------------------------------------
    async def _rule_negotiation_stuck_7d(
        self,
        empresa_id: UUID,
        rule: AutomationRule,
        now: datetime,
        stats: EngineStats,
    ) -> None:
        cutoff = now - timedelta(days=NEGOTIATION_STUCK_DAYS)
        stmt = (
            select(SalesPipelineItem)
            .where(
                and_(
                    SalesPipelineItem.empresa_id == empresa_id,
                    SalesPipelineItem.stage == "negotiation",
                    SalesPipelineItem.stage_entered_at <= cutoff,
                )
            )
            .limit(500)
        )
        deals = list((await self.session.execute(stmt)).scalars())
        stats.scanned_deals += len(deals)
        cust_map = await self._customer_map([d.customer_id for d in deals])
        for d in deals:
            cust = cust_map.get(d.customer_id) if d.customer_id else None
            days = int((now - d.stage_entered_at).total_seconds() // 86_400)
            ai_prio, ai_reason, ai_action, ai_score = self.ai.recommend(
                RULE_003, customer=cust, deal=d
            )
            priority = self._priority_from(rule, ai_prio)
            title = f"Negociación estancada: {d.title}"
            task = await self._create_task(
                empresa_id=empresa_id,
                rule=rule,
                title=title,
                description=(
                    f"Deal lleva {days} días en 'negotiation'. "
                    f"Valor estimado {d.estimated_value}."
                ),
                task_type="follow_up",
                priority=priority,
                due_date=self._due_in(24, now),
                customer_id=d.customer_id,
                pipeline_item_id=d.id,
                conversation_id=d.conversation_id,
                ai_reason=ai_reason,
                ai_next_action=ai_action,
                ai_score=ai_score,
                stats=stats,
            )
            await self._create_event(
                empresa_id=empresa_id,
                rule=rule,
                event_type="negotiation_stuck",
                entity_type="pipeline_item",
                entity_id=d.id,
                severity=self._severity_from(rule, "warning"),
                payload={
                    "deal_id": str(d.id),
                    "title": d.title,
                    "days_in_stage": days,
                    "task_id": str(task.id) if task else None,
                },
                stats=stats,
            )

    # ------------------------------------------------------------------
    # RULE 004 — VIP_CUSTOMER_INACTIVE_30D
    # ------------------------------------------------------------------
    async def _rule_vip_inactive_30d(
        self,
        empresa_id: UUID,
        rule: AutomationRule,
        now: datetime,
        stats: EngineStats,
    ) -> None:
        cutoff = now - timedelta(days=VIP_INACTIVE_DAYS)
        # A "VIP customer" is any customer with a VIP-flagged open
        # deal, OR a customer whose lead_score is at the top of the
        # spectrum (>= 80). Both signals are read-only.
        stmt = (
            select(Cliente)
            .where(
                and_(
                    Cliente.empresa_id == empresa_id,
                    Cliente.deleted_at.is_(None),
                    or_(
                        Cliente.lead_score >= 80,
                        Cliente.id.in_(
                            select(SalesPipelineItem.customer_id).where(
                                and_(
                                    SalesPipelineItem.empresa_id == empresa_id,
                                    SalesPipelineItem.is_vip.is_(True),
                                    SalesPipelineItem.stage.in_(tuple(OPEN_STAGES)),
                                )
                            )
                        ),
                    ),
                    or_(
                        Cliente.last_interaction_at.is_(None),
                        Cliente.last_interaction_at < cutoff,
                    ),
                )
            )
            .limit(500)
        )
        customers = list((await self.session.execute(stmt)).scalars())
        stats.scanned_customers += len(customers)
        for c in customers:
            idle_d = (
                int((now - c.last_interaction_at).total_seconds() // 86_400)
                if c.last_interaction_at
                else VIP_INACTIVE_DAYS
            )
            ai_prio, ai_reason, ai_action, ai_score = self.ai.recommend(
                RULE_004,
                customer=c,
                deal=None,
            )
            priority = self._priority_from(rule, ai_prio)
            title = f"Recuperar cliente VIP: {c.full_name}"
            task = await self._create_task(
                empresa_id=empresa_id,
                rule=rule,
                title=title,
                description=(
                    f"VIP inactivo {idle_d} días (score "
                    f"{c.lead_score}). Campaña de recuperación."
                ),
                task_type="recovery",
                priority=priority,
                due_date=self._due_in(8, now),
                customer_id=c.id,
                pipeline_item_id=None,
                conversation_id=c.last_conversation_id,
                ai_reason=ai_reason,
                ai_next_action=ai_action,
                ai_score=ai_score,
                stats=stats,
            )
            await self._create_event(
                empresa_id=empresa_id,
                rule=rule,
                event_type="vip_inactive",
                entity_type="customer",
                entity_id=c.id,
                severity=self._severity_from(rule, "critical"),
                payload={
                    "customer_id": str(c.id),
                    "full_name": c.full_name,
                    "lead_score": c.lead_score,
                    "idle_days": idle_d,
                    "task_id": str(task.id) if task else None,
                },
                stats=stats,
            )

    # ------------------------------------------------------------------
    # RULE 005 — NEW_HIGH_VALUE_LEAD
    # ------------------------------------------------------------------
    async def _rule_new_high_value_lead(
        self,
        empresa_id: UUID,
        rule: AutomationRule,
        now: datetime,
        stats: EngineStats,
    ) -> None:
        window = now - timedelta(days=2)
        # A "new high value" deal is a recently created pipeline item
        # that is still in new_lead/contacted/qualified and has a high
        # estimated value, OR a customer with high LTV that just got
        # attached to a new deal.
        stmt = (
            select(SalesPipelineItem)
            .where(
                and_(
                    SalesPipelineItem.empresa_id == empresa_id,
                    SalesPipelineItem.created_at >= window,
                    SalesPipelineItem.stage.in_(
                        (NEW_LEAD_STAGE, "contacted", "qualified")
                    ),
                )
            )
            .limit(500)
        )
        deals = list((await self.session.execute(stmt)).scalars())
        stats.scanned_deals += len(deals)
        cust_map = await self._customer_map([d.customer_id for d in deals])
        for d in deals:
            cust = cust_map.get(d.customer_id) if d.customer_id else None
            ai_prio, ai_reason, ai_action, ai_score = self.ai.recommend(
                RULE_005,
                customer=cust,
                deal=d,
                lifetime_value=Decimal("0"),
            )
            # Only fire if the AI score clears a soft threshold
            if ai_score < 60:
                continue
            priority = self._priority_from(rule, ai_prio)
            title = (
                f"Nuevo lead de alto valor: {d.title}"
                f" ({d.estimated_value})"
            )
            task = await self._create_task(
                empresa_id=empresa_id,
                rule=rule,
                title=title,
                description=(
                    f"Nuevo lead con valor {d.estimated_value}. "
                    "Asignar a un ejecutivo senior."
                ),
                task_type="alert",
                priority=priority,
                due_date=self._due_in(2, now),
                customer_id=d.customer_id,
                pipeline_item_id=d.id,
                conversation_id=d.conversation_id,
                ai_reason=ai_reason,
                ai_next_action=ai_action,
                ai_score=ai_score,
                stats=stats,
            )
            await self._create_event(
                empresa_id=empresa_id,
                rule=rule,
                event_type="new_high_value_lead",
                entity_type="pipeline_item",
                entity_id=d.id,
                severity=self._severity_from(rule, "info"),
                payload={
                    "deal_id": str(d.id),
                    "title": d.title,
                    "estimated_value": float(d.estimated_value),
                    "task_id": str(task.id) if task else None,
                },
                stats=stats,
            )

    # ------------------------------------------------------------------
    # RULE 006 — PIPELINE_WON
    # ------------------------------------------------------------------
    async def _rule_pipeline_won(
        self,
        empresa_id: UUID,
        rule: AutomationRule,
        now: datetime,
        stats: EngineStats,
    ) -> None:
        window = now - timedelta(hours=24)
        stmt = (
            select(SalesPipelineItem)
            .where(
                and_(
                    SalesPipelineItem.empresa_id == empresa_id,
                    SalesPipelineItem.stage == WON_STAGE,
                    SalesPipelineItem.updated_at >= window,
                )
            )
            .limit(500)
        )
        deals = list((await self.session.execute(stmt)).scalars())
        stats.scanned_deals += len(deals)
        for d in deals:
            ai_prio, ai_reason, ai_action, ai_score = self.ai.recommend(
                RULE_006, customer=None, deal=d
            )
            priority = self._priority_from(rule, ai_prio)
            title = f"Ganado: {d.title}"
            task = await self._create_task(
                empresa_id=empresa_id,
                rule=rule,
                title=title,
                description=(
                    f"Deal ganado. Motivo: {d.won_reason or 'n/d'}. "
                    f"Valor: {d.estimated_value}."
                ),
                task_type="win_log",
                priority=priority,
                due_date=None,
                customer_id=d.customer_id,
                pipeline_item_id=d.id,
                conversation_id=d.conversation_id,
                ai_reason=ai_reason,
                ai_next_action=ai_action,
                ai_score=ai_score,
                stats=stats,
            )
            await self._create_event(
                empresa_id=empresa_id,
                rule=rule,
                event_type="pipeline_won",
                entity_type="pipeline_item",
                entity_id=d.id,
                severity=self._severity_from(rule, "info"),
                payload={
                    "deal_id": str(d.id),
                    "title": d.title,
                    "value": float(d.estimated_value),
                    "won_reason": d.won_reason,
                    "task_id": str(task.id) if task else None,
                },
                stats=stats,
            )

    # ------------------------------------------------------------------
    # RULE 007 — PIPELINE_LOST
    # ------------------------------------------------------------------
    async def _rule_pipeline_lost(
        self,
        empresa_id: UUID,
        rule: AutomationRule,
        now: datetime,
        stats: EngineStats,
    ) -> None:
        window = now - timedelta(hours=24)
        stmt = (
            select(SalesPipelineItem)
            .where(
                and_(
                    SalesPipelineItem.empresa_id == empresa_id,
                    SalesPipelineItem.stage == LOST_STAGE,
                    SalesPipelineItem.updated_at >= window,
                )
            )
            .limit(500)
        )
        deals = list((await self.session.execute(stmt)).scalars())
        stats.scanned_deals += len(deals)
        for d in deals:
            ai_prio, ai_reason, ai_action, ai_score = self.ai.recommend(
                RULE_007, customer=None, deal=d
            )
            priority = self._priority_from(rule, ai_prio)
            title = f"Perdido: {d.title}"
            task = await self._create_task(
                empresa_id=empresa_id,
                rule=rule,
                title=title,
                description=(
                    f"Deal perdido. Motivo: {d.lost_reason or 'n/d'}. "
                    "Agendar reactivación a 60 días."
                ),
                task_type="loss_log",
                priority=priority,
                due_date=self._due_in(48, now),
                customer_id=d.customer_id,
                pipeline_item_id=d.id,
                conversation_id=d.conversation_id,
                ai_reason=ai_reason,
                ai_next_action=ai_action,
                ai_score=ai_score,
                stats=stats,
            )
            await self._create_event(
                empresa_id=empresa_id,
                rule=rule,
                event_type="pipeline_lost",
                entity_type="pipeline_item",
                entity_id=d.id,
                severity=self._severity_from(rule, "warning"),
                payload={
                    "deal_id": str(d.id),
                    "title": d.title,
                    "value": float(d.estimated_value),
                    "lost_reason": d.lost_reason,
                    "task_id": str(task.id) if task else None,
                },
                stats=stats,
            )


__all__ = ["AutomationRuleEngine", "EngineStats"]
