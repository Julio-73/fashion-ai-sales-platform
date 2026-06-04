"""Pipeline automations — pure rule evaluation, no side effects.

We intentionally do NOT install DB triggers. Rules run on demand from
``/pipeline/alerts`` and are also re-evaluated on stage moves.

Rules implemented:
    STUCK_IN_STAGE       — open deal > 7 days in same stage
    COLD_LEAD            — no interaction in 14+ days and still open
    VIP_IGNORED          — VIP deal with no activity in 3 days
    HIGH_INTENT_SILENT   — AI score >= 75 but no movement in 5 days
    NEAR_BUDGET_OVERFLOW — single deal >= 50% of total open value
"""
from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Iterable
from uuid import UUID, uuid4

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.customers.models import Cliente
from app.modules.pipeline.ai import CommercialAI
from app.modules.pipeline.models import OPEN_STAGES, SalesPipelineItem
from app.modules.pipeline.schemas import PipelineAlert


SEVERITY_INFO = "info"
SEVERITY_WARNING = "warning"
SEVERITY_CRITICAL = "critical"


STUCK_DAYS = 7
COLD_DAYS = 14
VIP_IDLE_DAYS = 3
HIGH_INTENT_IDLE_DAYS = 5
NEAR_BUDGET_SHARE = 0.5


class AutomationEngine:
    """Evaluate pipeline rules. Stateless per request."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.ai = CommercialAI(session)

    async def _stuck_in_stage(
        self, deal: SalesPipelineItem, now: datetime
    ) -> PipelineAlert | None:
        if deal.stage not in OPEN_STAGES:
            return None
        days = (now - deal.stage_entered_at).days
        if days < STUCK_DAYS:
            return None
        return PipelineAlert(
            id=str(uuid4()),
            deal_id=deal.id,
            deal_title=deal.title,
            customer_id=deal.customer_id,
            rule="STUCK_IN_STAGE",
            severity=SEVERITY_WARNING if days < 14 else SEVERITY_CRITICAL,
            message=f"Deal lleva {days} días en la etapa '{deal.stage}'.",
            suggested_action="Revisar bloqueos, hacer outreach o reasignar.",
            stage=deal.stage,
            days_in_stage=days,
            created_at=now,
        )

    async def _cold_lead(
        self,
        deal: SalesPipelineItem,
        customer: Cliente | None,
        now: datetime,
    ) -> PipelineAlert | None:
        if customer is None or customer.last_interaction_at is None:
            return None
        if deal.stage not in OPEN_STAGES:
            return None
        days = (now - customer.last_interaction_at).days
        if days < COLD_DAYS:
            return None
        return PipelineAlert(
            id=str(uuid4()),
            deal_id=deal.id,
            deal_title=deal.title,
            customer_id=deal.customer_id,
            rule="COLD_LEAD",
            severity=SEVERITY_WARNING,
            message=f"Cliente sin interacción hace {days} días.",
            suggested_action="Programar reactivación con oferta personalizada.",
            stage=deal.stage,
            days_in_stage=days,
            created_at=now,
        )

    async def _vip_ignored(
        self, deal: SalesPipelineItem, now: datetime
    ) -> PipelineAlert | None:
        if not deal.is_vip or deal.stage not in OPEN_STAGES:
            return None
        days = (now - deal.last_activity_at).days
        if days < VIP_IDLE_DAYS:
            return None
        return PipelineAlert(
            id=str(uuid4()),
            deal_id=deal.id,
            deal_title=deal.title,
            customer_id=deal.customer_id,
            rule="VIP_IGNORED",
            severity=SEVERITY_CRITICAL,
            message=f"VIP sin actividad hace {days} días.",
            suggested_action="Asignar a un senior y contactar en < 24 h.",
            stage=deal.stage,
            days_in_stage=days,
            created_at=now,
        )

    async def _high_intent_silent(
        self,
        deal: SalesPipelineItem,
        now: datetime,
    ) -> PipelineAlert | None:
        if deal.stage not in OPEN_STAGES:
            return None
        total, _ = (await self.ai.score_deal(deal))[:2]
        if total < 75:
            return None
        days = (now - deal.last_activity_at).days
        if days < HIGH_INTENT_IDLE_DAYS:
            return None
        return PipelineAlert(
            id=str(uuid4()),
            deal_id=deal.id,
            deal_title=deal.title,
            customer_id=deal.customer_id,
            rule="HIGH_INTENT_SILENT",
            severity=SEVERITY_CRITICAL,
            message=f"Score {total} pero sin movimiento en {days} días.",
            suggested_action="Empujar a 'negotiation' o contactar HOY.",
            stage=deal.stage,
            days_in_stage=days,
            created_at=now,
        )

    async def _near_budget_overflow(
        self,
        deal: SalesPipelineItem,
        total_open_value: Decimal,
        now: datetime,
    ) -> PipelineAlert | None:
        if deal.stage not in OPEN_STAGES:
            return None
        if total_open_value <= 0:
            return None
        share = float(deal.estimated_value) / float(total_open_value)
        if share < NEAR_BUDGET_SHARE:
            return None
        return PipelineAlert(
            id=str(uuid4()),
            deal_id=deal.id,
            deal_title=deal.title,
            customer_id=deal.customer_id,
            rule="NEAR_BUDGET_OVERFLOW",
            severity=SEVERITY_INFO,
            message=(
                f"Este deal representa {share * 100:.0f}% del valor abierto del "
                "pipeline."
            ),
            suggested_action="Diversificar el pipeline o asignar ejecutivo dedicado.",
            stage=deal.stage,
            days_in_stage=(now - deal.stage_entered_at).days,
            created_at=now,
        )

    async def _sum_open_value(self, empresa_id: UUID) -> Decimal:
        stmt = select(
            func.coalesce(func.sum(SalesPipelineItem.estimated_value), 0)
        ).where(
            and_(
                SalesPipelineItem.empresa_id == empresa_id,
                SalesPipelineItem.stage.in_(tuple(OPEN_STAGES)),
            )
        )
        v = (await self.session.execute(stmt)).scalar() or 0
        return Decimal(str(v))

    async def _load_customers(
        self, ids: Iterable[UUID]
    ) -> dict[UUID, Cliente]:
        ids = list({i for i in ids if i is not None})
        if not ids:
            return {}
        stmt = select(Cliente).where(Cliente.id.in_(ids))
        return {c.id: c for c in (await self.session.execute(stmt)).scalars()}

    async def evaluate(
        self, empresa_id: UUID, deals: list[SalesPipelineItem]
    ) -> list[PipelineAlert]:
        now = datetime.utcnow()
        total_open_value = await self._sum_open_value(empresa_id)
        customers = await self._load_customers(
            [d.customer_id for d in deals if d.customer_id]
        )
        alerts: list[PipelineAlert] = []
        for d in deals:
            cust = customers.get(d.customer_id) if d.customer_id else None
            for fn in (
                lambda: self._stuck_in_stage(d, now),
                lambda: self._cold_lead(d, cust, now),
                lambda: self._vip_ignored(d, now),
                lambda: self._high_intent_silent(d, now),
                lambda: self._near_budget_overflow(d, total_open_value, now),
            ):
                try:
                    a = await fn()
                    if a is not None:
                        alerts.append(a)
                except Exception:  # pragma: no cover - robustness
                    continue
        # Most severe first
        order = {SEVERITY_CRITICAL: 0, SEVERITY_WARNING: 1, SEVERITY_INFO: 2}
        alerts.sort(key=lambda a: (order.get(a.severity, 9), -a.days_in_stage))
        return alerts


__all__ = [
    "AutomationEngine",
    "STUCK_DAYS",
    "COLD_DAYS",
    "VIP_IDLE_DAYS",
    "HIGH_INTENT_IDLE_DAYS",
    "NEAR_BUDGET_SHARE",
    "SEVERITY_INFO",
    "SEVERITY_WARNING",
    "SEVERITY_CRITICAL",
]
