import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.context.repositories.sales_context_repository import (
    SalesContextRepository,
)
from app.conversations.models import ConversationCore, MessageCore
from app.modules.customers.models import Cliente
from app.sales.classifiers.intent_classifier import IntentClassifier
from app.sales.scoring.lead_scorer import LeadScorer

logger = logging.getLogger("ai_sales_agent.ai.intelligence.conversion")


class ConversionPredictor:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._sales_repo = SalesContextRepository(session)
        self._classifier = IntentClassifier()
        self._scorer = LeadScorer()

    async def predict_conversion(
        self, *, empresa_id: UUID, customer_id: UUID
    ) -> dict:
        customer = await self._get_customer(empresa_id, customer_id)
        if customer is None:
            return {"probability": "low", "score": 0, "factors": []}

        prob = await self._sales_repo.get_conversion_probability(
            empresa_id=empresa_id, customer_id=customer_id
        )
        trend = await self._sales_repo.get_buying_intent_trend(
            empresa_id=empresa_id, customer_id=customer_id
        )
        churn = await self._sales_repo.get_churn_risk(
            empresa_id=empresa_id, customer_id=customer_id
        )
        stage = await self._sales_repo.get_negotiation_stage(
            empresa_id=empresa_id, customer_id=customer_id
        )
        score = customer.lead_score or 0

        factors = []
        if trend == "increasing":
            factors.append("intención de compra creciente")
        if churn == "low" and score >= 20:
            factors.append("bajo riesgo de abandono con buen score")
        if stage in ("active_negotiation", "advanced"):
            factors.append(f"etapa avanzada: {stage}")
        if score >= 40:
            factors.append("lead score alto")
        if customer.priority == "hot":
            factors.append("lead caliente")

        return {
            "probability": prob,
            "score": score,
            "trend": trend,
            "churn_risk": churn,
            "negotiation_stage": stage,
            "factors": factors,
            "days_since_last_interaction": self._days_since(customer.last_interaction_at),
        }

    async def predict_multiple(
        self, *, empresa_id: UUID, customer_ids: list[UUID]
    ) -> list[dict]:
        results = []
        for cid in customer_ids:
            prediction = await self.predict_conversion(
                empresa_id=empresa_id, customer_id=cid
            )
            prediction["customer_id"] = str(cid)
            results.append(prediction)
        return sorted(results, key=lambda r: r.get("score", 0), reverse=True)

    async def batch_lead_scoring(
        self, *, empresa_id: UUID, customer_ids: list[UUID]
    ) -> list[dict]:
        scored = []
        for cid in customer_ids:
            customer = await self._get_customer(empresa_id, cid)
            if customer is None:
                continue
            conv_count = await self._get_conv_count(empresa_id, cid)
            msg_count = await self._get_msg_count(empresa_id, cid)
            messages = await self._get_customer_messages(empresa_id, cid, limit=50)
            intent_labels = []
            for m in messages:
                intents = self._classifier.classify_all(m.content)
                intent_labels.extend(i.value for i, _ in intents)
            score = self._scorer.calculate_score(
                intent_labels=intent_labels,
                message_count=msg_count,
                conversation_count=conv_count,
                last_interaction_at=customer.last_interaction_at,
            )
            priority = self._scorer.score_to_priority(score)
            scored.append({
                "customer_id": str(cid),
                "full_name": customer.full_name,
                "score": score,
                "priority": priority,
                "status": customer.lead_status,
            })
        return sorted(scored, key=lambda r: r["score"], reverse=True)

    async def _get_customer(self, empresa_id: UUID, customer_id: UUID) -> Cliente | None:
        from sqlalchemy import select
        result = await self._session.execute(
            select(Cliente).where(
                Cliente.empresa_id == empresa_id,
                Cliente.id == customer_id,
                Cliente.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def _get_conv_count(self, empresa_id: UUID, customer_id: UUID) -> int:
        from sqlalchemy import func, select
        result = await self._session.execute(
            select(func.count()).select_from(
                select(ConversationCore)
                .where(
                    ConversationCore.empresa_id == empresa_id,
                    ConversationCore.customer_id == customer_id,
                )
                .subquery()
            )
        )
        return int(result.scalar_one())

    async def _get_msg_count(self, empresa_id: UUID, customer_id: UUID) -> int:
        from sqlalchemy import func, select
        result = await self._session.execute(
            select(func.count()).select_from(
                select(MessageCore)
                .join(ConversationCore, MessageCore.conversation_id == ConversationCore.id)
                .where(
                    ConversationCore.empresa_id == empresa_id,
                    ConversationCore.customer_id == customer_id,
                )
                .subquery()
            )
        )
        return int(result.scalar_one())

    async def _get_customer_messages(
        self, empresa_id: UUID, customer_id: UUID, limit: int
    ) -> list[MessageCore]:
        from sqlalchemy import select
        result = await self._session.execute(
            select(MessageCore)
            .join(ConversationCore, MessageCore.conversation_id == ConversationCore.id)
            .where(
                ConversationCore.empresa_id == empresa_id,
                ConversationCore.customer_id == customer_id,
            )
            .order_by(MessageCore.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    def _days_since(self, dt: datetime | None) -> int | None:
        if dt is None:
            return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return (datetime.now(UTC) - dt).days
