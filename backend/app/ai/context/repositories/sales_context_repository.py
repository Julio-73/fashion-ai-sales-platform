import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.conversations.models import ConversationCore
from app.modules.customers.models import Cliente
from app.sales.classifiers.intent_classifier import IntentClassifier
from app.sales.scoring.lead_scorer import LeadScorer

logger = logging.getLogger("ai_sales_agent.ai.context.repositories.sales")


class SalesContextRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._classifier = IntentClassifier()
        self._scorer = LeadScorer()

    async def get_conversion_probability(
        self, *, empresa_id: UUID, customer_id: UUID
    ) -> str:
        customer = await self._get_customer(empresa_id, customer_id)
        if customer is None:
            return "low"
        score = customer.lead_score or 0
        priority = customer.priority or "cold"
        status = customer.lead_status
        if score >= 60:
            return "high"
        if score >= 30:
            return "medium"
        if status == "negotiating":
            return "medium"
        return "low"

    async def get_negotiation_stage(
        self, *, empresa_id: UUID, customer_id: UUID
    ) -> str:
        customer = await self._get_customer(empresa_id, customer_id)
        if customer is None:
            return "initial"
        status = customer.lead_status
        score = customer.lead_score or 0
        if status == "won":
            return "closed_won"
        if status == "lost":
            return "closed_lost"
        if status == "negotiating":
            return "active_negotiation"
        if score >= 40:
            return "advanced"
        if score >= 20:
            return "engaged"
        if score >= 5:
            return "interested"
        return "initial"

    async def get_discount_sensitivity(
        self, *, empresa_id: UUID, customer_id: UUID
    ) -> str:
        customer = await self._get_customer(empresa_id, customer_id)
        if customer is None:
            return "unknown"
        tags = [t.lower() for t in (customer.tags or [])]
        if any("discount" in t or "descuento" in t or "negoti" in t or "regateo" in t for t in tags):
            return "high"
        if customer.lead_status == "negotiating":
            return "medium"
        if customer.priority == "hot":
            return "low"
        return "unknown"

    async def get_buying_intent_trend(
        self, *, empresa_id: UUID, customer_id: UUID
    ) -> str:
        result = await self._session.execute(
            select(ConversationCore.updated_at)
            .where(
                ConversationCore.empresa_id == empresa_id,
                ConversationCore.customer_id == customer_id,
            )
            .order_by(ConversationCore.updated_at.desc())
            .limit(20)
        )
        timestamps = [row.updated_at for row in result if row.updated_at]
        if len(timestamps) < 3:
            return "stable"
        now = datetime.now(UTC)
        recent = sum(1 for t in timestamps if (now - t.replace(tzinfo=UTC) if t.tzinfo is None else (now - t)).days <= 3)
        mid = sum(1 for t in timestamps if 3 < ((now - t.replace(tzinfo=UTC) if t.tzinfo is None else (now - t)).days) <= 7)
        if recent >= mid:
            return "increasing"
        if mid > recent:
            return "decreasing"
        return "stable"

    async def get_churn_risk(
        self, *, empresa_id: UUID, customer_id: UUID
    ) -> str:
        customer = await self._get_customer(empresa_id, customer_id)
        if customer is None:
            return "low"
        if customer.last_interaction_at:
            last = customer.last_interaction_at
            if last.tzinfo is None:
                last = last.replace(tzinfo=UTC)
            days_since = (datetime.now(UTC) - last).days
            if days_since > 60:
                return "high"
            if days_since > 30:
                return "medium"
        score = customer.lead_score or 0
        if score < 5 and customer.lead_status not in ("won", "lost"):
            return "medium"
        return "low"

    async def is_hot_lead(
        self, *, empresa_id: UUID, customer_id: UUID
    ) -> bool:
        customer = await self._get_customer(empresa_id, customer_id)
        if customer is None:
            return False
        return customer.priority == "hot" or (customer.lead_score or 0) >= 50

    async def is_premium_customer(
        self, *, empresa_id: UUID, customer_id: UUID
    ) -> bool:
        customer = await self._get_customer(empresa_id, customer_id)
        if customer is None:
            return False
        tags = [t.lower() for t in (customer.tags or [])]
        return "vip" in tags or "premium" in tags or "recurrente" in tags

    async def get_lead_score_evolution(
        self, *, empresa_id: UUID, customer_id: UUID
    ) -> list[dict]:
        result = await self._session.execute(
            select(Cliente.lead_score, Cliente.updated_at)
            .where(
                Cliente.empresa_id == empresa_id,
                Cliente.id == customer_id,
                Cliente.deleted_at.is_(None),
            )
            .order_by(Cliente.updated_at.desc())
            .limit(10)
        )
        return [
            {"score": row.lead_score, "timestamp": row.updated_at.isoformat() if row.updated_at else None}
            for row in result
        ]

    async def _get_customer(
        self, empresa_id: UUID, customer_id: UUID
    ) -> Cliente | None:
        result = await self._session.execute(
            select(Cliente).where(
                Cliente.empresa_id == empresa_id,
                Cliente.id == customer_id,
                Cliente.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()
