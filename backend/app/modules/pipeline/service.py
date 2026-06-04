"""Service layer — business orchestration."""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.modules.customers.models import Cliente
from app.modules.orders.models import Order
from app.modules.pipeline.ai import CommercialAI
from app.modules.pipeline.automations import AutomationEngine
from app.modules.pipeline.models import (
    CLOSED_STAGES,
    OPEN_STAGES,
    PIPELINE_STAGE_VALUES,
    SalesPipelineItem,
    WON_STAGE,
    is_valid_stage,
)
from app.modules.pipeline.repository import PipelineRepository
from app.modules.pipeline.schemas import (
    AIScoreBreakdown,
    CustomerSummary,
    PipelineAIScoreResponse,
    PipelineAlert,
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


STAGE_CATALOG: list[PipelineStageInfo] = [
    PipelineStageInfo(
        key="new_lead",
        label="Nuevo lead",
        description="Lead captado que aún no recibió respuesta.",
        is_open=True,
        is_terminal=False,
        order=0,
        default_probability=10,
        color="#94a3b8",
    ),
    PipelineStageInfo(
        key="contacted",
        label="Contactado",
        description="Primer outreach realizado, esperando respuesta.",
        is_open=True,
        is_terminal=False,
        order=1,
        default_probability=25,
        color="#60a5fa",
    ),
    PipelineStageInfo(
        key="qualified",
        label="Calificado",
        description="Confirmó interés y encaje con la oferta.",
        is_open=True,
        is_terminal=False,
        order=2,
        default_probability=45,
        color="#38bdf8",
    ),
    PipelineStageInfo(
        key="proposal",
        label="Propuesta",
        description="Cotización o propuesta enviada.",
        is_open=True,
        is_terminal=False,
        order=3,
        default_probability=65,
        color="#a78bfa",
    ),
    PipelineStageInfo(
        key="negotiation",
        label="Negociación",
        description="Negociando términos, objeciones o precio final.",
        is_open=True,
        is_terminal=False,
        order=4,
        default_probability=80,
        color="#f59e0b",
    ),
    PipelineStageInfo(
        key="won",
        label="Ganado",
        description="Deal cerrado como ganado.",
        is_open=False,
        is_terminal=True,
        order=5,
        default_probability=100,
        color="#22c55e",
    ),
    PipelineStageInfo(
        key="lost",
        label="Perdido",
        description="Deal perdido o descartado.",
        is_open=False,
        is_terminal=True,
        order=6,
        default_probability=0,
        color="#ef4444",
    ),
]


_DEFAULT_PROBABILITY = {s.key: s.default_probability for s in STAGE_CATALOG}


class PipelineService:
    """Business orchestration for the pipeline module."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = PipelineRepository(session)
        self.ai = CommercialAI(session)
        self.automations = AutomationEngine(session)

    # ------------------------------------------------------------------
    # Static catalog
    # ------------------------------------------------------------------
    @staticmethod
    def list_stages() -> list[PipelineStageInfo]:
        return list(STAGE_CATALOG)

    @staticmethod
    def stage_info(stage: str) -> PipelineStageInfo | None:
        if not is_valid_stage(stage):
            return None
        for s in STAGE_CATALOG:
            if s.key == stage:
                return s
        return None

    # ------------------------------------------------------------------
    # Enrichment helpers
    # ------------------------------------------------------------------
    async def _customers_map(
        self, ids: list[UUID | None]
    ) -> dict[UUID, Cliente]:
        clean = [i for i in ids if i is not None]
        if not clean:
            return {}
        stmt = select(Cliente).where(Cliente.id.in_(clean))
        return {c.id: c for c in (await self.session.execute(stmt)).scalars()}

    async def _orders_stats(
        self, empresa_id: UUID, customers: dict[UUID, Cliente]
    ) -> dict[UUID, tuple[int, Decimal]]:
        names = [c.full_name for c in customers.values() if c.full_name]
        if not names:
            return {cid: (0, Decimal("0")) for cid in customers}
        stmt = select(
            Order.customer_name,
            func.count(Order.id),
            func.coalesce(func.sum(Order.total), 0),
        ).where(
            and_(
                Order.empresa_id == empresa_id,
                Order.customer_name.in_(names),
                Order.status != "cancelled",
            )
        ).group_by(Order.customer_name)
        rows = (await self.session.execute(stmt)).all()
        by_name: dict[str, tuple[int, Decimal]] = {
            r[0]: (int(r[1] or 0), Decimal(str(r[2] or 0))) for r in rows
        }
        out: dict[UUID, tuple[int, Decimal]] = {}
        for cid, c in customers.items():
            out[cid] = by_name.get(c.full_name, (0, Decimal("0"))) if c.full_name else (0, Decimal("0"))
        return out

    async def _to_response(
        self,
        deal: SalesPipelineItem,
        customer_map: dict[UUID, Cliente],
        order_map: dict[UUID, tuple[int, Decimal]],
        include_ai: bool = False,
    ) -> PipelineItemResponse:
        cust = customer_map.get(deal.customer_id) if deal.customer_id else None
        oc, ltv = order_map.get(deal.customer_id, (0, Decimal("0"))) if cust else (0, Decimal("0"))
        customer_summary: CustomerSummary | None = None
        if cust is not None:
            customer_summary = CustomerSummary(
                id=cust.id,
                full_name=cust.full_name,
                email=cust.email,
                phone=cust.phone,
                whatsapp=cust.whatsapp,
                lead_status=cust.lead_status,
                priority=cust.priority,
                lead_score=int(cust.lead_score or 0),
                is_vip=bool(deal.is_vip) or bool(cust.lead_score and cust.lead_score >= 80),
                last_interaction_at=cust.last_interaction_at,
                conversation_count=int(cust.conversation_count or 0),
                lifetime_value=ltv,
                orders_count=oc,
            )
        ai_breakdown: AIScoreBreakdown | None = None
        if include_ai:
            total, breakdown, _ = await self.ai.score_deal(deal)
            ai_breakdown = breakdown
        return PipelineItemResponse(
            id=deal.id,
            empresa_id=deal.empresa_id,
            customer_id=deal.customer_id,
            conversation_id=deal.conversation_id,
            order_id=deal.order_id,
            title=deal.title,
            estimated_value=deal.estimated_value,
            probability=deal.probability,
            stage=deal.stage,
            stage_entered_at=deal.stage_entered_at,
            last_activity_at=deal.last_activity_at,
            notes=deal.notes,
            won_reason=deal.won_reason,
            lost_reason=deal.lost_reason,
            position=deal.position,
            channel=deal.channel,
            is_vip=deal.is_vip,
            created_at=deal.created_at,
            updated_at=deal.updated_at,
            customer=customer_summary,
            ai_score=ai_breakdown,
        )

    async def _enrich(
        self, deals: list[SalesPipelineItem], include_ai: bool
    ) -> list[PipelineItemResponse]:
        if not deals:
            return []
        customers = await self._customers_map([d.customer_id for d in deals])
        order_map = await self._orders_stats(
            next(iter(customers.values())).empresa_id if customers else deals[0].empresa_id,
            customers,
        )
        return [
            await self._to_response(d, customers, order_map, include_ai=include_ai)
            for d in deals
        ]

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------
    async def create(
        self, empresa_id: UUID, payload: PipelineItemCreate
    ) -> PipelineItemResponse:
        if not is_valid_stage(payload.stage):
            raise AppError(
                code="invalid_stage",
                message=f"unknown stage '{payload.stage}'",
                status_code=400,
            )
        # Last position in the column
        same_stage = await self.repo.list_items(
            empresa_id=empresa_id, stage=payload.stage, limit=500
        )
        next_position = (max((d.position for d in same_stage), default=-1)) + 1
        item = await self.repo.create(
            empresa_id=empresa_id,
            customer_id=payload.customer_id,
            conversation_id=payload.conversation_id,
            order_id=payload.order_id,
            title=payload.title,
            estimated_value=payload.estimated_value,
            probability=payload.probability,
            stage=payload.stage,
            notes=payload.notes,
            channel=payload.channel,
            is_vip=payload.is_vip,
            position=next_position,
        )
        await self.session.commit()
        enriched = await self._enrich([item], include_ai=True)
        return enriched[0]

    async def list_board(
        self,
        empresa_id: UUID,
        *,
        stage: str | None = None,
        is_open: bool | None = None,
        search: str | None = None,
    ) -> PipelineBoardResponse:
        deals = await self.repo.list_items(
            empresa_id=empresa_id,
            stage=stage,
            is_open=is_open,
            search=search,
            limit=500,
        )
        items = await self._enrich(deals, include_ai=False)
        counts = await self.repo.count_by_stage(empresa_id)
        values = await self.repo.sum_value_by_stage(empresa_id)
        return PipelineBoardResponse(
            items=items,
            total=len(items),
            by_stage={k: counts.get(k, 0) for k in PIPELINE_STAGE_VALUES},
            value_by_stage={k: values.get(k, 0.0) for k in PIPELINE_STAGE_VALUES},
        )

    async def get(self, empresa_id: UUID, deal_id: UUID) -> PipelineItemResponse:
        deal = await self.repo.get(empresa_id, deal_id)
        if deal is None:
            raise AppError(code="not_found", message="Deal not found", status_code=404)
        enriched = await self._enrich([deal], include_ai=True)
        return enriched[0]

    async def update(
        self, empresa_id: UUID, deal_id: UUID, payload: PipelineItemUpdate
    ) -> PipelineItemResponse:
        deal = await self.repo.get(empresa_id, deal_id)
        if deal is None:
            raise AppError(code="not_found", message="Deal not found", status_code=404)
        changes = payload.model_dump(exclude_unset=True, exclude_none=False)
        # ``None`` vs "field not provided" — keep ``None`` as an explicit clear.
        for k in list(changes.keys()):
            v = changes[k]
            if v is None and k not in {"customer_id", "conversation_id", "order_id", "notes", "channel"}:
                changes.pop(k)
        deal = await self.repo.update(item=deal, changes=changes)
        await self.session.commit()
        enriched = await self._enrich([deal], include_ai=True)
        return enriched[0]

    async def move_stage(
        self, empresa_id: UUID, deal_id: UUID, payload: PipelineItemMoveStage
    ) -> PipelineItemResponse:
        if not is_valid_stage(payload.target_stage):
            raise AppError(
                code="invalid_stage",
                message=f"unknown stage '{payload.target_stage}'",
                status_code=400,
            )
        deal = await self.repo.get(empresa_id, deal_id)
        if deal is None:
            raise AppError(code="not_found", message="Deal not found", status_code=404)
        # Backwards moves from terminal stages are blocked.
        if deal.stage in CLOSED_STAGES and payload.target_stage in OPEN_STAGES:
            raise AppError(
                code="invalid_transition",
                message="No se puede reabrir un deal cerrado.",
                status_code=400,
            )
        probability = payload.probability
        if probability is None and payload.target_stage != deal.stage:
            probability = _DEFAULT_PROBABILITY.get(payload.target_stage, deal.probability)
        deal = await self.repo.move_stage(
            item=deal,
            target_stage=payload.target_stage,
            probability=probability,
            notes=payload.notes,
            won_reason=payload.won_reason,
            lost_reason=payload.lost_reason,
        )
        await self.session.commit()
        enriched = await self._enrich([deal], include_ai=True)
        return enriched[0]

    async def delete(self, empresa_id: UUID, deal_id: UUID) -> None:
        deal = await self.repo.get(empresa_id, deal_id)
        if deal is None:
            raise AppError(code="not_found", message="Deal not found", status_code=404)
        await self.repo.soft_delete(deal)
        await self.session.commit()

    # ------------------------------------------------------------------
    # Metrics, funnel, alerts
    # ------------------------------------------------------------------
    async def metrics(self, empresa_id: UUID) -> PipelineMetricsResponse:
        agg = await self.repo.aggregate_metrics(empresa_id)
        counts = agg["counts"]
        values = agg["values"]

        total_open = sum(counts.get(s, 0) for s in OPEN_STAGES)
        total_won = counts.get("won", 0)
        total_lost = counts.get("lost", 0)
        total_closed = total_won + total_lost
        conversion = (total_won / total_closed * 100.0) if total_closed else 0.0
        open_value = sum(values.get(s, 0) for s in OPEN_STAGES)
        won_value = values.get("won", 0)
        lost_value = values.get("lost", 0)
        avg_value = (
            (open_value + won_value + lost_value)
            / max(1, total_open + total_closed)
        )

        # Average time to close: won + lost
        avg_close = await self._average_time_to_close(empresa_id)
        # Average time in current stage (open)
        avg_in_stage = await self._average_time_in_stage(empresa_id)

        alerts = await self._alert_count(empresa_id)

        # By stage breakdown (count, value, avg value)
        by_stage: dict[str, dict[str, float]] = {}
        for s in PIPELINE_STAGE_VALUES:
            c = counts.get(s, 0)
            v = values.get(s, 0.0)
            by_stage[s] = {
                "count": float(c),
                "value": v,
                "average_value": (v / c) if c else 0.0,
            }

        # By channel and by priority (priority is per customer)
        by_channel = await self._by_channel(empresa_id, values, counts)
        by_priority = await self._by_priority(empresa_id, counts)

        return PipelineMetricsResponse(
            total_open=total_open,
            total_closed_won=total_won,
            total_closed_lost=total_lost,
            open_value=round(open_value, 2),
            weighted_open_value=round(agg["weighted_open"], 2),
            won_value=round(won_value, 2),
            lost_value=round(lost_value, 2),
            conversion_rate_pct=round(conversion, 2),
            average_deal_value=round(avg_value, 2),
            average_time_to_close_days=round(avg_close, 2),
            average_time_in_current_stage_days=round(avg_in_stage, 2),
            oldest_unstuck_days=agg["oldest_in_stage_days"],
            alerts_count=alerts,
            by_stage={k: {kk: round(vv, 2) for kk, vv in v.items()} for k, v in by_stage.items()},
            by_channel={k: {kk: round(vv, 2) for kk, vv in v.items()} for k, v in by_channel.items()},
            by_priority={k: {kk: round(vv, 2) for kk, vv in v.items()} for k, v in by_priority.items()},
        )

    async def funnel(self, empresa_id: UUID) -> PipelineFunnelResponse:
        counts = await self.repo.count_by_stage(empresa_id)
        values = await self.repo.sum_value_by_stage(empresa_id)
        stages: list[dict[str, Any]] = []
        for s in STAGE_CATALOG:
            stages.append(
                {
                    "key": s.key,
                    "label": s.label,
                    "color": s.color,
                    "count": counts.get(s.key, 0),
                    "value": round(values.get(s.key, 0.0), 2),
                }
            )
        total_open = sum(counts.get(s.key, 0) for s in STAGE_CATALOG if s.is_open)
        total_closed = sum(counts.get(s.key, 0) for s in STAGE_CATALOG if s.is_terminal)
        return PipelineFunnelResponse(
            stages=stages,
            total_open=total_open,
            total_closed=total_closed,
            won_value=round(values.get("won", 0.0), 2),
            lost_value=round(values.get("lost", 0.0), 2),
        )

    async def alerts(self, empresa_id: UUID) -> PipelineAlertsResponse:
        deals = await self.repo.list_items(empresa_id=empresa_id, is_open=True, limit=500)
        result = await self.automations.evaluate(empresa_id, list(deals))
        return PipelineAlertsResponse(alerts=result, total=len(result))

    async def recommendations(
        self, empresa_id: UUID
    ) -> PipelineRecommendationsResponse:
        deals = await self.repo.list_items(
            empresa_id=empresa_id, is_open=True, limit=500
        )
        recs: list[PipelineRecommendation] = []
        for d in deals:
            recs.append(await self.ai.recommend(d))
        recs.sort(key=lambda r: -r.score)
        return PipelineRecommendationsResponse(recommendations=recs, total=len(recs))

    async def score(self, empresa_id: UUID, deal_id: UUID) -> PipelineAIScoreResponse:
        deal = await self.repo.get(empresa_id, deal_id)
        if deal is None:
            raise AppError(code="not_found", message="Deal not found", status_code=404)
        total, breakdown, _ = await self.ai.score_deal(deal)
        return PipelineAIScoreResponse(deal_id=deal.id, score=total, breakdown=breakdown)

    async def dashboard(self, empresa_id: UUID) -> PipelineDashboardResponse:
        metrics = await self.metrics(empresa_id)
        funnel = await self.funnel(empresa_id)
        alerts = await self.alerts(empresa_id)
        # Top deals by AI score, limit 5
        deals = await self.repo.list_items(
            empresa_id=empresa_id, is_open=True, limit=50
        )
        scored = []
        for d in deals:
            total, _, _ = await self.ai.score_deal(d)
            scored.append((total, d))
        scored.sort(key=lambda t: -t[0])
        top_ids = {d.id for _, d in scored[:5]}
        top_deals = [d for d in deals if d.id in top_ids]
        top_deals_resp = await self._enrich(top_deals, include_ai=True)
        # Sort response by score desc
        score_map = {d.id: s for s, d in scored}
        top_deals_resp.sort(key=lambda r: -score_map.get(r.id, 0))
        return PipelineDashboardResponse(
            metrics=metrics,
            funnel=funnel,
            alerts=alerts,
            top_deals=top_deals_resp,
            generated_at=datetime.utcnow(),
        )

    # ------------------------------------------------------------------
    # Internals for metrics
    # ------------------------------------------------------------------
    async def _average_time_to_close(self, empresa_id: UUID) -> float:
        days_expr = func.extract(
            "epoch", SalesPipelineItem.updated_at - SalesPipelineItem.created_at
        ) / 86400.0
        stmt = select(func.coalesce(func.avg(days_expr), 0)).where(
            and_(
                SalesPipelineItem.empresa_id == empresa_id,
                SalesPipelineItem.stage.in_((WON_STAGE, "lost")),
            )
        )
        v = (await self.session.execute(stmt)).scalar() or 0
        return float(v)

    async def _average_time_in_stage(self, empresa_id: UUID) -> float:
        days_expr = func.extract(
            "epoch", func.now() - SalesPipelineItem.stage_entered_at
        ) / 86400.0
        stmt = select(func.coalesce(func.avg(days_expr), 0)).where(
            SalesPipelineItem.empresa_id == empresa_id,
            SalesPipelineItem.stage.in_(tuple(OPEN_STAGES)),
        )
        v = (await self.session.execute(stmt)).scalar() or 0
        return float(v)

    async def _alert_count(self, empresa_id: UUID) -> int:
        deals = await self.repo.list_items(empresa_id=empresa_id, is_open=True, limit=500)
        a = await self.automations.evaluate(empresa_id, list(deals))
        return len(a)

    async def _by_channel(
        self,
        empresa_id: UUID,
        values: dict[str, float],
        counts: dict[str, int],
    ) -> dict[str, dict[str, float]]:
        # Sum value by channel for open deals
        stmt = select(
            SalesPipelineItem.channel,
            func.coalesce(func.sum(SalesPipelineItem.estimated_value), 0),
            func.count(SalesPipelineItem.id),
        ).where(
            SalesPipelineItem.empresa_id == empresa_id
        ).group_by(SalesPipelineItem.channel)
        rows = (await self.session.execute(stmt)).all()
        out: dict[str, dict[str, float]] = {}
        for ch, v, c in rows:
            key = ch or "unknown"
            out[key] = {
                "count": float(c or 0),
                "value": float(v or 0),
            }
        return out

    async def _by_priority(
        self, empresa_id: UUID, counts: dict[str, int]
    ) -> dict[str, dict[str, float]]:
        # Join customers → pipeline items to get priority
        stmt = select(
            Cliente.priority,
            func.count(SalesPipelineItem.id),
        ).select_from(SalesPipelineItem).join(
            Cliente, Cliente.id == SalesPipelineItem.customer_id, isouter=True
        ).where(
            SalesPipelineItem.empresa_id == empresa_id
        ).group_by(Cliente.priority)
        rows = (await self.session.execute(stmt)).all()
        out: dict[str, dict[str, float]] = {}
        for prio, c in rows:
            key = prio or "unknown"
            out[key] = {"count": float(c or 0)}
        return out


__all__ = [
    "PipelineService",
    "STAGE_CATALOG",
]
