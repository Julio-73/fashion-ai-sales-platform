import logging
from uuid import UUID

from app.ai.classifiers.intent_classifier import IntentClassifierService
from app.ai_live.repository import ConversationAIRepository
from app.ai_live.schemas import SuggestedReply
from app.ai_live.services.handoff_service import HandoffService
from app.modules.conversations.schemas import ConversationDetailResponse
from app.ai.services.llm_service import LLMService


logger = logging.getLogger("ai_sales_agent.ai_live.suggestions")


class AISuggestionsService:
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

    async def suggest_replies(
        self,
        *,
        empresa_id: UUID,
        conversation_id: UUID,
        conversation_detail: ConversationDetailResponse | None = None,
    ) -> list[SuggestedReply]:
        if not conversation_detail:
            from app.database.session import get_db_session
            from app.modules.conversations.repository import ConversationRepository as ConvRepo

            async for session in get_db_session():
                conv_repo = ConvRepo(session=session)
                conversation = await conv_repo.get_conversation_by_id(
                    empresa_id=empresa_id, conversation_id=conversation_id
                )
                if not conversation:
                    return self._fallback_suggestions()
                messages, _ = await conv_repo.list_messages(
                    empresa_id=empresa_id, conversation_id=conversation_id, limit=100, offset=0
                )
                conversation_detail = ConversationDetailResponse(
                    id=conversation.id,
                    empresa_id=conversation.empresa_id,
                    cliente_id=conversation.cliente_id,
                    asunto=conversation.asunto,
                    canal=conversation.canal,
                    estado=conversation.estado,
                    deleted_at=conversation.deleted_at,
                    created_at=conversation.created_at,
                    updated_at=conversation.updated_at,
                    messages=list(messages),
                )
                break

        last_messages = [m.content for m in conversation_detail.messages[-5:]]
        last_user_msg = last_messages[-1] if last_messages else ""

        if not last_user_msg:
            return self._fallback_suggestions()

        classification = await self._classifier.classify(last_user_msg)
        intent = classification.intent.value
        confidence = classification.confidence

        shall_escalate, escalate_reason = await self._handoff_service.evaluate_escalation(
            empresa_id=empresa_id,
            message=last_user_msg,
            intent=intent,
            lead_score=0.0,
        )

        if shall_escalate:
            return [
                SuggestedReply(
                    text="Gracias por tu mensaje. Te conectamos con un agente humano que te atenderá personalmente.",
                    confidence=0.95,
                    reasoning=f"Escalado automático: {escalate_reason}",
                ),
            ]

        state = await self._repository.get_or_create_state(
            empresa_id=empresa_id, conversation_id=conversation_id
        )

        if state.ai_enabled and self._llm_service.is_configured:
            suggestions = await self._generate_llm_suggestions(
                last_user_msg=last_user_msg,
                intent=intent,
                confidence=confidence,
                last_messages=last_messages,
            )
        else:
            suggestions = self._template_suggestions(intent, last_user_msg)

        await self._repository.update_state(
            state=state,
            last_detected_intent=intent,
            ai_confidence=confidence,
        )

        await self._repository.add_event(
            empresa_id=empresa_id,
            conversation_id=conversation_id,
            event_type="suggestion_generated",
            payload={"intent": intent, "suggestion_count": len(suggestions)},
        )

        return suggestions

    async def _generate_llm_suggestions(
        self,
        *,
        last_user_msg: str,
        intent: str,
        confidence: float,
        last_messages: list[str],
    ) -> list[SuggestedReply]:
        history = " | ".join(last_messages[:-1]) if len(last_messages) > 1 else "Sin historial"

        prompt = (
            f"Eres un asistente de ventas para una empresa de moda. "
            f"Genera 3 respuestas cortas y profesionales al mensaje del cliente. "
            f"Intención detectada: {intent} (confianza: {confidence:.2f}). "
            f"Historial: {history}. "
            f"Mensaje del cliente: {last_user_msg}\n\n"
            f"Responde SOLO con las 3 sugerencias, una por línea, precedidas por SR:"
        )

        try:
            response_text = await self._llm_service._provider.generate(
                system_prompt=prompt,
                user_message=last_user_msg,
                temperature=0.7,
                max_tokens=300,
            )

            lines = [ln.strip() for ln in response_text.split("\n") if ln.strip()]
            suggestions = []
            for line in lines:
                clean = line.removeprefix("SR:").removeprefix("sr:").strip().strip('"').strip("'")
                if clean and len(suggestions) < 3:
                    suggestions.append(
                        SuggestedReply(
                            text=clean,
                            confidence=round(confidence, 2),
                            reasoning=f"Basado en intent: {intent}",
                        )
                    )

            if suggestions:
                return suggestions
        except Exception:
            logger.exception("LLM suggestion generation failed")

        return self._template_suggestions(intent, last_user_msg)

    def _template_suggestions(self, intent: str, message: str) -> list[SuggestedReply]:
        templates: dict[str, list[str]] = {
            "pricing": [
                "Claro, te comparto los precios actualizados de nuestros productos.",
                "¿Te gustaría que te ayude a encontrar algo dentro de tu presupuesto?",
                "Tenemos opciones desde precios accesibles hasta colección premium.",
            ],
            "purchase_intent": [
                "Excelente elección. ¿Te ayudo a procesar tu pedido?",
                "Me encantaría ayudarte con tu compra. ¿Qué producto te interesa?",
                "Podemos agendar tu pedido ahora mismo si lo deseas.",
            ],
            "negotiation": [
                "Entiendo que buscas el mejor precio. Déjame ver qué opciones tenemos.",
                "Podemos ofrecerte condiciones especiales en esta compra.",
                "Hablemos con nuestro equipo para darte la mejor oferta posible.",
            ],
            "support": [
                "Lamento el inconveniente. Cuéntame más para ayudarte mejor.",
                "Voy a revisar tu caso y te brindo una solución.",
                "¿Podrías indicarme tu número de pedido para revisarlo?",
            ],
            "delivery": [
                "Te ayudo a rastrear tu pedido. ¿Tienes el número de seguimiento?",
                "Los tiempos de entrega son de 3 a 5 días hábiles.",
                "¿Quieres que verifique el estado de tu envío?",
            ],
            "greeting": [
                "¡Hola! Bienvenido a nuestro servicio de atención al cliente.",
                "¿En qué puedo ayudarte hoy? Estoy aquí para lo que necesites.",
                "Cuéntame, ¿buscas algo en especial o tienes alguna consulta?",
            ],
            "product_question": [
                "Con gusto te doy los detalles del producto que te interesa.",
                "¿Hay alguna característica específica sobre la que quieras saber más?",
                "Te comparto la ficha completa del producto con todas sus especificaciones.",
            ],
            "sizing": [
                "Te ayudo con las tallas. Contamos con una guía detallada.",
                "¿Podrías indicarme qué producto te interesa para recomendarte la talla?",
                "Nuestra ropa tiene tabla de tallas. ¿Quieres que te la comparta?",
            ],
        }

        intent_templates = templates.get(intent, [
            "Gracias por tu mensaje. ¿En qué más puedo ayudarte?",
            "Quedo atento a cualquier otra consulta que tengas.",
            "Estoy aquí para ayudarte con lo que necesites.",
        ])

        return [
            SuggestedReply(text=t, confidence=0.75, reasoning=f"Template para intent: {intent}")
            for t in intent_templates
        ]

    def _fallback_suggestions(self) -> list[SuggestedReply]:
        return [
            SuggestedReply(
                text="Para ayudarte mejor, ¿podrías contarme más sobre tu consulta?",
                confidence=0.5,
                reasoning="Mensaje inicial sin contexto suficiente",
            ),
        ]
