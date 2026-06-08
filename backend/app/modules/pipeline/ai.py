"""Commercial AI — deterministic, no LLM, runs in microseconds.

Combines signals from:
    * ``clientes``  (lead_status, priority, lead_score, last_interaction_at)
    * ``conversation_ai_states`` (sentiment, urgency, lead_temperature)
    * ``orders``  (lifetime value, repeat purchases)
    * the deal itself (estimated_value, probability, stage, days_in_stage)

Output: a 0–100 score plus a textual recommendation.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_live.models import ConversationAIState
from app.modules.customers.models import Cliente
from app.modules.orders.models import Order
from app.modules.pipeline.models import (
    CLOSED_STAGES,
    SalesPipelineItem,
    WON_STAGE,
    LOST_STAGE,
)
from app.modules.pipeline.schemas import AIScoreBreakdown, PipelineRecommendation


# ---------------------------------------------------------------------------
# Pure scoring helpers (no I/O, easy to unit-test)
# ---------------------------------------------------------------------------
_INTENT_BOOST: dict[str, int] = {
    "buy": 95,
    "purchase": 90,
    "order": 88,
    "checkout": 90,
    "price": 70,
    "discount": 65,
    "shipping": 50,
    "return": 30,
    "complaint": 20,
    "support": 40,
    "greeting": 15,
}

_SENTIMENT_BIAS: dict[str, int] = {
    "positive": 80,
    "neutral": 50,
    "negative": 20,
}

_TEMPERATURE_BIAS: dict[str, int] = {
    "hot": 90,
    "warm": 60,
    "cold": 25,
}


def _clamp(v: int, lo: int = 0, hi: int = 100) -> int:
    return max(lo, min(hi, v))


def _intent_score(intent: str | None) -> int:
    if not intent:
        return 35
    key = intent.strip().lower()
    for k, v in _INTENT_BOOST.items():
        if k in key:
            return v
    return 35


def _sentiment_score(sentiment: str | None) -> int:
    if not sentiment:
        return 50
    return _SENTIMENT_BIAS.get(sentiment.strip().lower(), 50)


def _temperature_score(temp: str | None) -> int:
    if not temp:
        return 40
    return _TEMPERATURE_BIAS.get(temp.strip().lower(), 40)


def _recency_score(last_interaction_at: datetime | None, now: datetime) -> int:
    if last_interaction_at is None:
        return 20
    delta = now - last_interaction_at
    if delta <= timedelta(hours=24):
        return 95
    if delta <= timedelta(days=3):
        return 80
    if delta <= timedelta(days=7):
        return 60
    if delta <= timedelta(days=14):
        return 40
    if delta <= timedelta(days=30):
        return 25
    return 10


def _monetary_score(
    estimated_value: Decimal, lifetime_value: Decimal, orders_count: int
) -> int:
    base = float(estimated_value or 0) + float(lifetime_value or 0)
    if base <= 0:
        return 10
    # 0 → 10,  100 → 35,  500 → 60,  2_000 → 85,  10_000+ → 100
    score = 10 + (base ** 0.5) * 3
    if orders_count >= 2:
        score += 5
    if orders_count >= 5:
        score += 5
    return _clamp(int(score))


def _engagement_score(conv_count: int, urgency: float | None) -> int:
    base = min(conv_count, 10) * 8
    if urgency is not None:
        base += _clamp(int(urgency * 30))
    return _clamp(base)


def _days_since(when: datetime | None, now: datetime) -> int:
    """Whole calendar days between ``when`` and ``now``. ``0`` if missing."""
    if when is None:
        return 0
    delta = now - when
    if delta.total_seconds() <= 0:
        return 0
    return int(delta.total_seconds() // 86_400)


# ---------------------------------------------------------------------------
# Data classes used by the service layer
# ---------------------------------------------------------------------------
@dataclass
class DealContext:
    """Snapshot of everything we need to score a deal."""

    deal: SalesPipelineItem
    customer: Cliente | None
    ai_state: ConversationAIState | None
    orders_count: int
    lifetime_value: Decimal
    now: datetime


class CommercialAI:
    """Stateless scorer — instantiated per request."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ------------------------------------------------------------------
    # I/O helpers (read-only against frozen modules)
    # ------------------------------------------------------------------
    async def _customer(self, empresa_id: UUID, customer_id: UUID | None) -> Cliente | None:
        if customer_id is None:
            return None
        stmt = select(Cliente).where(
            and_(
                Cliente.empresa_id == empresa_id,
                Cliente.id == customer_id,
            )
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def _ai_state(self, conversation_id: UUID | None) -> ConversationAIState | None:
        if conversation_id is None:
            return None
        stmt = select(ConversationAIState).where(
            ConversationAIState.conversation_id == conversation_id
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def _order_stats(
        self, empresa_id: UUID, customer: Cliente | None
    ) -> tuple[int, Decimal]:
        """Return ``(orders_count, lifetime_value)`` for a customer."""
        if customer is None:
            return 0, Decimal("0")
        if customer.full_name:
            stmt = select(
                func.count(Order.id),
                func.coalesce(func.sum(Order.total), 0),
            ).where(
                and_(
                    Order.empresa_id == empresa_id,
                    Order.customer_name == customer.full_name,
                    Order.status != "cancelled",
                )
            )
            row = (await self.session.execute(stmt)).one()
            return int(row[0] or 0), Decimal(str(row[1] or 0))
        return 0, Decimal("0")

    async def _gather(self, deal: SalesPipelineItem) -> DealContext:
        customer = await self._customer(deal.empresa_id, deal.customer_id)
        ai_state = await self._ai_state(deal.conversation_id)
        orders_count, ltv = await self._order_stats(deal.empresa_id, customer)
        return DealContext(
            deal=deal,
            customer=customer,
            ai_state=ai_state,
            orders_count=orders_count,
            lifetime_value=ltv,
            now=datetime.utcnow(),
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    async def score_deal(
        self, deal: SalesPipelineItem
    ) -> tuple[int, AIScoreBreakdown, list[str]]:
        ctx = await self._gather(deal)

        intent = _intent_score(ctx.ai_state.last_detected_intent if ctx.ai_state else None)
        sentiment = _sentiment_score(ctx.ai_state.sentiment if ctx.ai_state else None)
        engagement = _engagement_score(
            ctx.customer.conversation_count if ctx.customer else 0,
            ctx.ai_state.urgency_score if ctx.ai_state else None,
        )
        recency = _recency_score(
            ctx.customer.last_interaction_at if ctx.customer else None, ctx.now
        )
        monetary = _monetary_score(
            deal.estimated_value, ctx.lifetime_value, ctx.orders_count
        )

        # Weighted blend
        total = (
            intent * 0.28
            + sentiment * 0.12
            + engagement * 0.20
            + recency * 0.18
            + monetary * 0.22
        )
        total = _clamp(int(total))

        rationale: list[str] = []
        if intent >= 70:
            rationale.append("Cliente con alta intención de compra")
        elif intent <= 30:
            rationale.append("Intención de compra débil o inexistente")
        if sentiment == "negative":
            rationale.append("Sentimiento negativo — atender con prioridad")
        elif sentiment == "positive":
            rationale.append("Sentimiento positivo — buen momento para avanzar")
        if recency >= 80:
            rationale.append("Cliente activo en las últimas 24 h")
        else:
            days_silent = (
                _days_since(ctx.customer.last_interaction_at, ctx.now)
                if ctx.customer else 0
            )
            if days_silent >= 5:
                rationale.append(
                    f"Cliente sin seguimiento hace {days_silent} días"
                )
            elif recency <= 25:
                rationale.append("Sin interacción en más de 30 días — riesgo de fuga")
        if monetary >= 70:
            rationale.append("Valor del deal alto o cliente con LTV relevante")
        if engagement >= 70:
            rationale.append("Cliente con múltiples conversaciones")
        if ctx.ai_state and ctx.ai_state.escalation_required:
            rationale.append("IA Live marcó escalación a humano")
        if ctx.customer and ctx.customer.priority == "hot":
            rationale.append("Lead HOT según CRM")

        # FASE 4 — extra recommendation templates requested by spec.
        # All signals are computed from data the pipeline already reads.
        if ctx.orders_count >= 3:
            rationale.append("Cliente con historial de compras recurrentes")
        if (
            monetary >= 70
            and ctx.orders_count >= 2
            and recency >= 60
        ):
            rationale.append("Posible cliente VIP — asignar ejecutivo dedicado")
        elif deal.is_vip and ctx.orders_count >= 1:
            rationale.append("Cliente VIP con compras previas — proteger relación")
        if (
            deal.stage == "negotiation"
            and (ctx.now - deal.stage_entered_at).days > 7
        ):
            rationale.append("Lead estancado en negociación — más de 7 días sin avanzar")

        breakdown = AIScoreBreakdown(
            total=total,
            intent=intent,
            engagement=engagement,
            recency=recency,
            monetary=monetary,
            sentiment=sentiment,
            rationale=rationale,
        )
        return total, breakdown, rationale

    async def recommend(
        self, deal: SalesPipelineItem
    ) -> PipelineRecommendation:
        total, breakdown, rationale = await self.score_deal(deal)
        next_action = _next_best_action(deal, breakdown)
        suggested_channel = _suggested_channel(deal, breakdown)
        suggested_stage = _suggested_stage(deal, breakdown)
        return PipelineRecommendation(
            deal_id=deal.id,
            score=total,
            breakdown=breakdown,
            next_best_action=next_action,
            suggested_channel=suggested_channel,
            suggested_stage=suggested_stage,
            notes=rationale,
        )

    async def score_many(
        self, deals: list[SalesPipelineItem]
    ) -> dict[UUID, tuple[int, AIScoreBreakdown]]:
        out: dict[UUID, tuple[int, AIScoreBreakdown]] = {}
        for d in deals:
            total, breakdown, _ = await self.score_deal(d)
            out[d.id] = (total, breakdown)
        return out


# ---------------------------------------------------------------------------
# Recommendation helpers (pure)
# ---------------------------------------------------------------------------
def _next_best_action(deal: SalesPipelineItem, b: AIScoreBreakdown) -> str:
    if deal.stage in CLOSED_STAGES or deal.stage in (WON_STAGE, LOST_STAGE):
        return "Deal cerrado — no requiere acción."
    if b.intent >= 80 and b.engagement >= 60:
        return "Enviar propuesta formal con precio bloqueado por 48 h."
    if b.recency <= 25:
        return "Reactivar con WhatsApp: oferta personalizada + pregunta abierta."
    if b.intent <= 30 and b.sentiment < 40:
        return "Asignar a un humano senior — objeciones serias detectadas."
    if b.monetary >= 70 and b.engagement >= 50:
        return "Ofrecer descuento por volumen o bundle para acelerar cierre."
    if b.intent >= 60:
        return "Pedir confirmación verbal y agendar llamada de cierre."
    if b.recency >= 80:
        return "Hacer follow-up hoy — cliente caliente recién activo."
    return "Mantener en nurturing; revisar en 48 h."


def _suggested_channel(deal: SalesPipelineItem, b: AIScoreBreakdown) -> str | None:
    if b.sentiment < 40:
        return "Llamada"
    if b.intent >= 70:
        return "WhatsApp"
    if b.engagement >= 50:
        return "Email"
    if deal.channel:
        return deal.channel
    return None


def _suggested_stage(deal: SalesPipelineItem, b: AIScoreBreakdown) -> str | None:
    if deal.stage in CLOSED_STAGES or deal.stage in (WON_STAGE, LOST_STAGE):
        return None
    if b.intent >= 80 and deal.stage in {"new_lead", "contacted", "qualified"}:
        return "proposal"
    if b.intent <= 30 and b.sentiment < 30 and deal.stage not in ("lost",):
        return "lost"
    if b.total >= 75 and deal.stage == "negotiation":
        return "won"
    return None


# Constants re-exported to allow the service layer to import only from ai.
__all__ = [
    "CommercialAI",
    "DealContext",
    "_intent_score",
    "_sentiment_score",
    "_temperature_score",
    "_recency_score",
    "_monetary_score",
    "_engagement_score",
    "_days_since",
]
