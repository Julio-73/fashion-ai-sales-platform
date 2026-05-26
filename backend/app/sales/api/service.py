from __future__ import annotations

import logging
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import Select, func, or_, select, text, union
from sqlalchemy.ext.asyncio import AsyncSession

from app.conversations.models import ConversationCore, MessageCore
from app.core.errors import AppError
from app.core.security.dependencies import TenantContext
from app.modules.customers.models import Cliente
from app.sales.api.schemas import (
    ActivityEvent,
    AnalyzeMessageResponse,
    ConversationMetrics,
    CustomerRecommendation,
    CustomerSalesProfileResponse,
    IntentCount,
    SalesActivityResponse,
    SalesInsightsResponse,
    SalesRecommendationsResponse,
    TopCustomer,
    TopLead,
    TopLeadsResponse,
)
from app.sales.classifiers.intent_classifier import IntentClassifier
from app.sales.intents.intent import IntentType
from app.sales.rules.sales_rules import RuleContext, SalesRulesEngine
from app.sales.scoring.lead_scorer import LeadScorer
from app.sales.services.sales_intelligence_service import SalesIntelligenceService

logger = logging.getLogger("ai_sales_agent.sales_api")


def _priority_order(priority: str) -> int:
    return {"hot": 0, "warm": 1, "cool": 2, "cold": 3}.get(priority, 99)


def _compute_activity_level(last_interaction_at: datetime | None, conversation_count: int) -> str:
    if last_interaction_at is None:
        return "inactive"
    now = datetime.now(UTC)
    if last_interaction_at.tzinfo is None:
        last_interaction_at = last_interaction_at.replace(tzinfo=UTC)
    days_since = (now - last_interaction_at).days
    if days_since <= 1:
        return "very_active"
    if days_since <= 7:
        return "active"
    if days_since <= 14:
        return "moderate"
    if days_since <= 30:
        return "low"
    return "inactive"


def _conversion_probability(score: int, priority: str, status: str) -> str:
    if score >= 60:
        return "high"
    if score >= 30:
        return "medium"
    if status == "negotiating":
        return "medium"
    return "low"


def _sales_summary(
    lead_status: str,
    priority: str,
    score: int,
    conversation_count: int,
    last_interaction_at: datetime | None,
) -> str:
    if priority == "hot":
        return "Cliente caliente con alta probabilidad de cierre. Priorizar seguimiento inmediato."
    if lead_status == "won":
        return "Cliente convertido. Cliente fidelizado con historial de compra."
    if lead_status == "lost":
        return "Cliente perdido. Evaluar estrategia de recuperación."
    if priority == "warm" and conversation_count >= 3:
        return "Cliente interesado con múltiples interacciones. Avanzar hacia negociación."
    if score >= 20:
        return "Cliente con interés detectado. Mantener contacto y nutrir relación."
    if last_interaction_at and (datetime.now(UTC) - last_interaction_at.replace(tzinfo=UTC)).days > 30:
        return "Cliente inactivo. Reactivar con campaña de re-engagement."
    return "Cliente en etapa inicial. Continuar seguimiento."


class SalesAPIService:
    def __init__(
        self,
        session: AsyncSession,
        classifier: IntentClassifier | None = None,
        scorer: LeadScorer | None = None,
        rules_engine: SalesRulesEngine | None = None,
        sales_intelligence: SalesIntelligenceService | None = None,
    ) -> None:
        self._session = session
        self._classifier = classifier or IntentClassifier()
        self._scorer = scorer or LeadScorer()
        self._rules_engine = rules_engine or SalesRulesEngine()
        self._sales_intelligence = sales_intelligence or SalesIntelligenceService(
            classifier=self._classifier,
            scorer=self._scorer,
            rules_engine=self._rules_engine,
        )

    # ── Helpers ──────────────────────────────────────────────

    def _customer_query(self, empresa_id: UUID) -> Select:
        return select(Cliente).where(
            Cliente.empresa_id == empresa_id,
            Cliente.deleted_at.is_(None),
        )

    async def _get_customer(self, empresa_id: UUID, customer_id: UUID) -> Cliente:
        result = await self._session.execute(
            self._customer_query(empresa_id).where(Cliente.id == customer_id)
        )
        customer = result.scalar_one_or_none()
        if customer is None:
            raise AppError(code="customer_not_found", message="Customer not found", status_code=404)
        return customer

    async def _get_conversation_count(self, empresa_id: UUID, customer_id: UUID) -> int:
        result = await self._session.execute(
            select(func.count()).select_from(
                select(ConversationCore).where(
                    ConversationCore.empresa_id == empresa_id,
                    ConversationCore.customer_id == customer_id,
                ).subquery()
            )
        )
        return int(result.scalar_one())

    async def _get_message_count(self, empresa_id: UUID, customer_id: UUID) -> int:
        result = await self._session.execute(
            select(func.count()).select_from(
                select(MessageCore)
                .join(ConversationCore, MessageCore.conversation_id == ConversationCore.id)
                .where(
                    ConversationCore.empresa_id == empresa_id,
                    ConversationCore.customer_id == customer_id,
                ).subquery()
            )
        )
        return int(result.scalar_one())

    async def _get_last_message(
        self, empresa_id: UUID, customer_id: UUID
    ) -> tuple[str | None, datetime | None]:
        result = await self._session.execute(
            select(MessageCore.content, MessageCore.created_at)
            .join(ConversationCore, MessageCore.conversation_id == ConversationCore.id)
            .where(
                ConversationCore.empresa_id == empresa_id,
                ConversationCore.customer_id == customer_id,
            )
            .order_by(MessageCore.created_at.desc())
            .limit(1)
        )
        row = result.one_or_none()
        if row:
            return row.content, row.created_at
        return None, None

    async def _get_conversations_for_customers(
        self, empresa_id: UUID, customer_ids: list[UUID]
    ) -> dict[UUID, int]:
        if not customer_ids:
            return {}
        result = await self._session.execute(
            select(ConversationCore.customer_id, func.count().label("cnt"))
            .where(
                ConversationCore.empresa_id == empresa_id,
                ConversationCore.customer_id.in_(customer_ids),
            )
            .group_by(ConversationCore.customer_id)
        )
        return {row.customer_id: int(row.cnt) for row in result}

    # ── 1. Insights ─────────────────────────────────────────

    async def get_insights(self, tenant: TenantContext) -> SalesInsightsResponse:
        empresa_id = tenant.empresa_id
        customers_result = await self._session.execute(
            self._customer_query(empresa_id).order_by(Cliente.lead_score.desc())
        )
        customers: Sequence[Cliente] = customers_result.scalars().all()

        hot_leads = [c for c in customers if c.priority == "hot"]
        interested = [c for c in customers if c.lead_status == "interested"]
        negotiation = [c for c in customers if c.lead_status == "negotiating"]
        converted = [c for c in customers if c.lead_status == "won"]

        sorted_by_score = sorted(customers, key=lambda c: c.lead_score or 0, reverse=True)
        top_customers = [
            TopCustomer(
                customer_id=str(c.id),
                full_name=c.full_name,
                lead_score=c.lead_score or 0,
                priority=c.priority or "cold",
                lead_status=c.lead_status,
                last_interaction_at=c.last_interaction_at,
            )
            for c in sorted_by_score[:10]
        ]

        high_priority = [
            TopCustomer(
                customer_id=str(c.id),
                full_name=c.full_name,
                lead_score=c.lead_score or 0,
                priority=c.priority or "cold",
                lead_status=c.lead_status,
                last_interaction_at=c.last_interaction_at,
            )
            for c in sorted(customers, key=lambda c: _priority_order(c.priority or "cold"))[:10]
        ]

        message_result = await self._session.execute(
            select(MessageCore.content).limit(500)
        )
        all_messages: list[str] = [row.content for row in message_result if row.content]
        intent_counts: dict[str, int] = {}
        for msg in all_messages:
            intents = self._classifier.classify_all(msg)
            for intent_type, _ in intents:
                key = intent_type.value
                intent_counts[key] = intent_counts.get(key, 0) + 1

        sorted_intents = sorted(intent_counts.items(), key=lambda x: x[1], reverse=True)
        most_detected = [
            IntentCount(intent=intent, count=count) for intent, count in sorted_intents[:10]
        ]

        recent_cutoff = datetime.now(UTC) - timedelta(days=7)
        recent_result = await self._session.execute(
            select(func.count()).select_from(
                select(ConversationCore).where(
                    ConversationCore.empresa_id == empresa_id,
                    ConversationCore.updated_at >= recent_cutoff,
                ).subquery()
            )
        )
        recent_activity = int(recent_result.scalar_one())

        return SalesInsightsResponse(
            total_hot_leads=len(hot_leads),
            total_interested=len(interested),
            total_negotiation=len(negotiation),
            total_converted=len(converted),
            top_customers=top_customers,
            high_priority_customers=high_priority,
            most_detected_intents=most_detected,
            recent_sales_activity=recent_activity,
        )

    # ── 2. Customer Sales Profile ────────────────────────────

    async def get_customer_profile(
        self, tenant: TenantContext, customer_id: UUID
    ) -> CustomerSalesProfileResponse:
        empresa_id = tenant.empresa_id
        customer = await self._get_customer(empresa_id, customer_id)

        conv_count = await self._get_conversation_count(empresa_id, customer_id)
        msg_count = await self._get_message_count(empresa_id, customer_id)
        last_msg_content, last_msg_at = await self._get_last_message(empresa_id, customer_id)

        messages_result = await self._session.execute(
            select(MessageCore.content)
            .join(ConversationCore, MessageCore.conversation_id == ConversationCore.id)
            .where(
                ConversationCore.empresa_id == empresa_id,
                ConversationCore.customer_id == customer_id,
            )
            .limit(200)
        )
        detected_intents: set[str] = set()
        for row in messages_result:
            intents = self._classifier.classify_all(row.content)
            for intent_type, _ in intents:
                detected_intents.add(intent_type.value)

        activity_level = _compute_activity_level(customer.last_interaction_at, conv_count)
        summary = _sales_summary(
            customer.lead_status,
            customer.priority or "cold",
            customer.lead_score or 0,
            conv_count,
            customer.last_interaction_at,
        )

        return CustomerSalesProfileResponse(
            customer_id=str(customer.id),
            full_name=customer.full_name,
            email=customer.email,
            phone=customer.phone,
            lead_score=customer.lead_score or 0,
            lead_status=customer.lead_status,
            priority=customer.priority or "cold",
            tags=customer.tags or [],
            detected_intents=sorted(detected_intents),
            activity_level=activity_level,
            last_interaction_at=customer.last_interaction_at,
            conversation_metrics=ConversationMetrics(
                total_conversations=conv_count,
                total_messages=msg_count,
                last_message_at=last_msg_at,
                last_message_content=last_msg_content,
            ),
            sales_summary=summary,
        )

    # ── 3. Analyze Message ───────────────────────────────────

    async def analyze_message(
        self, tenant: TenantContext, customer_id: UUID, message: str
    ) -> AnalyzeMessageResponse:
        empresa_id = tenant.empresa_id
        customer = await self._get_customer(empresa_id, customer_id)

        primary_intent, weight = self._classifier.classify(message)
        all_intents = self._classifier.classify_all(message)
        intent_labels = [i.value for i, _ in all_intents]

        conv_count = await self._get_conversation_count(empresa_id, customer_id)
        msg_count = await self._get_message_count(empresa_id, customer_id)

        score = self._scorer.calculate_score(
            intent_labels=intent_labels,
            message_count=msg_count + 1,
            conversation_count=conv_count,
            last_interaction_at=customer.last_interaction_at,
        )

        score_impact = self._scorer._signal_map.get(primary_intent.value, 0) if primary_intent != IntentType.unknown else 0

        priority = self._scorer.score_to_priority(score)

        rule_context = RuleContext(
            empresa_id=empresa_id,
            customer_id=customer_id,
            current_lead_status=customer.lead_status,
            current_priority=priority,
            current_score=score,
            conversation_count=conv_count,
            last_intents=intent_labels,
            existing_tags=tuple(customer.tags or []),
        )
        rule_results = self._rules_engine.evaluate_all(rule_context)
        suggested_status = None
        for rr in rule_results:
            if rr.suggested_lead_status:
                suggested_status = rr.suggested_lead_status
                break

        recommended_actions: dict[str, str] = {
            "purchase_intent": "Contactar inmediatamente con catálogo y precios.",
            "negotiation_intent": "Preparar propuesta con descuento y condiciones.",
            "pricing_intent": "Enviar lista de precios y opciones de pago.",
            "product_interest": "Enviar catálogo de productos relacionados.",
            "shipping_intent": "Informar tiempos y costos de envío.",
            "support_intent": "Derivar a soporte o resolver consulta técnica.",
            "greeting": "Responder saludo y preguntar cómo podemos ayudar.",
        }
        recommended_action = recommended_actions.get(
            primary_intent.value, "Revisar conversación y responder según contexto."
        )

        predicted_status = suggested_status or (
            "negotiating" if score >= 30 and customer.lead_status == "interested" else
            "interested" if score >= 15 and customer.lead_status == "new" else
            customer.lead_status
        )

        return AnalyzeMessageResponse(
            detected_intent=primary_intent,
            score_impact=score_impact,
            recommended_action=recommended_action,
            lead_status_prediction=predicted_status,
        )

    # ── 4. Recommendations ──────────────────────────────────

    async def get_recommendations(self, tenant: TenantContext) -> SalesRecommendationsResponse:
        empresa_id = tenant.empresa_id
        customers_result = await self._session.execute(
            self._customer_query(empresa_id).order_by(Cliente.lead_score.desc())
        )
        customers: Sequence[Cliente] = customers_result.scalars().all()

        now = datetime.now(UTC)
        follow_up: list[CustomerRecommendation] = []
        hot_leads: list[CustomerRecommendation] = []
        negotiation_leads: list[CustomerRecommendation] = []
        inactive: list[CustomerRecommendation] = []
        upsell: list[CustomerRecommendation] = []

        for c in customers:
            last_int = c.last_interaction_at
            if last_int and last_int.tzinfo is None:
                last_int = last_int.replace(tzinfo=UTC)
            days_since = (now - last_int).days if last_int else None

            score = c.lead_score or 0
            priority = c.priority or "cold"
            status = c.lead_status

            def _recommendation(cust: Cliente, reason: str) -> CustomerRecommendation:
                return CustomerRecommendation(
                    customer_id=str(cust.id),
                    full_name=cust.full_name,
                    lead_score=score,
                    priority=priority,
                    lead_status=status,
                    reason=reason,
                    days_since_last_interaction=days_since,
                )

            if priority == "hot":
                hot_leads.append(_recommendation(c, "Lead caliente con alta prioridad de cierre."))

            if status == "negotiating":
                negotiation_leads.append(_recommendation(c, "En negociación. Requiere seguimiento."))

            if days_since is not None and days_since > 14 and status not in ("won", "lost"):
                inactive.append(_recommendation(c, f"Cliente inactivo ({days_since} días sin interacción)."))

            if score >= 20 and days_since is not None and days_since <= 7 and status not in ("won", "lost"):
                follow_up.append(_recommendation(c, "Cliente con actividad e interés reciente."))

            if status == "won" and days_since is not None and days_since > 30:
                upsell.append(_recommendation(c, "Cliente fidelizado apto para upselling."))

            if priority in ("warm", "hot") and status not in ("won", "lost") and c.conversation_count >= 2:
                was_already = any(
                    r.customer_id == str(c.id) for r in follow_up
                )
                if not was_already:
                    follow_up.append(_recommendation(c, "Lead con buen score e interacción recurrente."))

        return SalesRecommendationsResponse(
            customers_to_follow_up=sorted(follow_up, key=lambda r: r.lead_score, reverse=True),
            hot_leads=sorted(hot_leads, key=lambda r: r.lead_score, reverse=True),
            negotiation_leads=sorted(negotiation_leads, key=lambda r: r.lead_score, reverse=True),
            inactive_customers=sorted(inactive, key=lambda r: r.days_since_last_interaction or 0, reverse=True),
            upsell_opportunities=sorted(upsell, key=lambda r: r.lead_score, reverse=True),
        )

    # ── 5. Top Leads ─────────────────────────────────────────

    async def get_top_leads(self, tenant: TenantContext, limit: int = 50) -> TopLeadsResponse:
        empresa_id = tenant.empresa_id
        customers_result = await self._session.execute(
            self._customer_query(empresa_id).order_by(
                Cliente.lead_score.desc().nulls_last(),
                Cliente.last_interaction_at.desc().nulls_last(),
            )
        )
        customers: Sequence[Cliente] = customers_result.scalars().all()

        customer_ids = [c.id for c in customers]
        conv_counts = await self._get_conversations_for_customers(empresa_id, customer_ids)

        leads = [
            TopLead(
                customer_id=str(c.id),
                full_name=c.full_name,
                lead_score=c.lead_score or 0,
                priority=c.priority or "cold",
                lead_status=c.lead_status,
                conversation_count=conv_counts.get(c.id, 0),
                last_interaction_at=c.last_interaction_at,
                conversion_probability=_conversion_probability(
                    c.lead_score or 0, c.priority or "cold", c.lead_status
                ),
            )
            for c in customers[:limit]
        ]

        return TopLeadsResponse(leads=leads, total=len(leads))

    # ── 6. Activity Timeline ─────────────────────────────────

    async def get_activity(self, tenant: TenantContext, limit: int = 50) -> SalesActivityResponse:
        empresa_id = tenant.empresa_id

        raw_sql = text("""
            SELECT event_type, description, timestamp, customer_id, customer_name FROM (
                SELECT
                    'message' AS event_type,
                    mc.content AS description,
                    mc.created_at AS timestamp,
                    cc.customer_id,
                    cl.full_name AS customer_name
                FROM messages_core mc
                JOIN conversations_core cc ON cc.id = mc.conversation_id
                LEFT JOIN clientes cl ON cl.id = cc.customer_id
                WHERE cc.empresa_id = :eid AND cl.deleted_at IS NULL

                UNION ALL

                SELECT
                    'conversation' AS event_type,
                    cc.last_message AS description,
                    cc.updated_at AS timestamp,
                    cc.customer_id,
                    cl.full_name AS customer_name
                FROM conversations_core cc
                LEFT JOIN clientes cl ON cl.id = cc.customer_id
                WHERE cc.empresa_id = :eid AND cl.deleted_at IS NULL
            ) AS activity
            ORDER BY timestamp DESC
            LIMIT :lim
        """)

        activity_result = await self._session.execute(raw_sql, {"eid": empresa_id, "lim": limit})

        events = [
            ActivityEvent(
                event_type=row.event_type,
                description=(row.description or "")[:200],
                timestamp=row.timestamp,
                customer_id=str(row.customer_id) if row.customer_id else None,
                customer_name=row.customer_name,
            )
            for row in activity_result
        ]

        return SalesActivityResponse(events=events, total=len(events))
