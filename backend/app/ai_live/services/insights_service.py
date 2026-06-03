import logging
from uuid import UUID

from app.ai.classifiers.intent_classifier import IntentClassifierService
from app.ai_live.repository import ConversationAIRepository
from app.ai_live.schemas import ConversationInsightsResponse
from app.ai_live.services.handoff_service import HandoffService
from app.ai.services.llm_service import LLMService


logger = logging.getLogger("ai_sales_agent.ai_live.insights")


URGENCY_MAP: dict[str, str] = {
    "angry_customer": "high",
    "refund_request": "high",
    "complaint": "high",
    "return_request": "medium",
    "negotiation": "medium",
    "negotiation_complex": "high",
    "support": "medium",
    "delivery": "medium",
    "pricing": "low",
    "greeting": "low",
    "product_question": "low",
    "sizing": "low",
    "purchase_intent": "high",
    "unknown": "low",
}

NEXT_STEP_MAP: dict[str, str] = {
    "pricing": "Compartir información de precios y ofertas disponibles",
    "purchase_intent": "Iniciar proceso de venta o agendar pedido",
    "negotiation": "Evaluar margen y ofrecer condiciones especiales",
    "support": "Recopilar detalles del problema y escalar si es necesario",
    "delivery": "Verificar número de seguimiento y estado del envío",
    "greeting": "Saludar cordialmente y preguntar cómo podemos ayudar",
    "product_question": "Proporcionar ficha técnica y detalles del producto",
    "sizing": "Compartir guía de tallas y recomendar según medidas",
    "return_request": "Iniciar proceso de devolución o escalar a soporte",
    "unknown": "Solicitar más información para entender la consulta",
}

RECOMMENDED_ACTION_MAP: dict[str, str] = {
    "pricing": "responder con catálogo y precios",
    "purchase_intent": "proceder con cierre de venta",
    "negotiation": "activar descuento si lead_score > 0.6",
    "support": "escalar a soporte si es necesario",
    "delivery": "consultar sistema de logística",
    "greeting": "iniciar conversación comercial",
    "product_question": "responder con detalle del producto",
    "sizing": "compartir guía de tallas",
    "return_request": "iniciar proceso de devolución",
    "unknown": "preguntar por necesidad específica",
}


class AIInsightsService:
    def __init__(
        self,
        repository: ConversationAIRepository,
        llm_service: LLMService,
        handoff_service: HandoffService,
    ) -> None:
        self._repository = repository
        self._llm_service = llm_service
        self._handoff_service = handoff_service
        self._classifier = IntentClassifierService()

    async def get_conversation_insights(
        self,
        *,
        empresa_id: UUID,
        conversation_id: UUID,
    ) -> ConversationInsightsResponse:
        state = await self._repository.get_or_create_state(
            empresa_id=empresa_id, conversation_id=conversation_id
        )

        from app.database.session import AsyncSessionLocal
        from app.modules.conversations.repository import ConversationRepository as ConvRepo

        async with AsyncSessionLocal() as session:
            conv_repo = ConvRepo(session=session)
            conversation = await conv_repo.get_conversation_by_id(
                empresa_id=empresa_id, conversation_id=conversation_id
            )
            if conversation:
                messages, _ = await conv_repo.list_messages(
                    empresa_id=empresa_id,
                    conversation_id=conversation_id,
                    limit=200,
                    offset=0,
                )
                msgs_list = list(messages)
            else:
                msgs_list = []

        last_user_msg = ""
        last_interaction = None
        for msg in reversed(msgs_list):
            if msg.role == "client":
                last_user_msg = msg.content
                last_interaction = msg.created_at.isoformat() if msg.created_at else None
                break

        intent = state.last_detected_intent or "unknown"
        urgency = URGENCY_MAP.get(intent, "low")
        recommended_action = RECOMMENDED_ACTION_MAP.get(intent, "revisar conversación")
        suggested_next_step = NEXT_STEP_MAP.get(intent, "Evaluar contexto de la conversación")

        shall_escalate, _ = await self._handoff_service.evaluate_escalation(
            empresa_id=empresa_id,
            message=last_user_msg or "",
            intent=intent,
            lead_score=0.0,
        )

        if last_user_msg:
            classification = await self._classifier.classify(last_user_msg)
            intent = classification.intent.value
            if classification.confidence >= 0.2:
                state.last_detected_intent = intent

        customer_activity = "active" if msgs_list else "inactive"

        return ConversationInsightsResponse(
            detected_intent=intent,
            urgency=urgency,
            lead_score=0.0,
            probability_to_buy=0.0,
            recommended_action=recommended_action,
            escalation_recommended=shall_escalate,
            customer_activity_level=customer_activity,
            last_interaction=last_interaction,
            suggested_next_step=suggested_next_step,
        )

    def _calculate_lead_temperature(self, state) -> str:
        if state.lead_temperature:
            return state.lead_temperature
        if state.urgency_score and state.urgency_score >= 0.7:
            return "hot"
        if state.urgency_score and state.urgency_score >= 0.4:
            return "warm"
        return "cold"
