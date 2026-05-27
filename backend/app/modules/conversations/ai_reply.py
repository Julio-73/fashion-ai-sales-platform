import logging
from uuid import UUID

from app.ai.classifiers.intent_classifier import IntentClassifierService
from app.ai.providers.openai_provider import OpenAIProvider
from app.modules.conversations.dtos import MessageDTO
from app.modules.conversations.models import Message as MessageModel
from app.modules.conversations.repository import ConversationRepository
from app.modules.conversations.schemas import MessageResponse
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("ai_sales_agent.conversations.ai_reply")


class AutoReplyGenerator:
    def __init__(
        self,
        session: AsyncSession,
        repository: ConversationRepository,
        provider: OpenAIProvider | None = None,
    ) -> None:
        self._session = session
        self._repository = repository
        self._provider = provider or OpenAIProvider()
        self._classifier = IntentClassifierService()

    async def generate_and_save(
        self,
        *,
        empresa_id: UUID,
        conversation_id: UUID,
    ) -> MessageResponse | None:
        conversation = await self._repository.get_conversation_by_id(
            empresa_id=empresa_id, conversation_id=conversation_id
        )
        if not conversation:
            return None

        messages, _ = await self._repository.list_messages(
            empresa_id=empresa_id, conversation_id=conversation_id, limit=50, offset=0
        )
        if not messages:
            return None

        last_messages = [m.content for m in messages[-5:]]
        last_user_msg = last_messages[-1] if last_messages else ""
        if not last_user_msg:
            return None

        response_text = await self._generate_response(
            last_user_msg=last_user_msg,
            last_messages=last_messages,
        )
        if not response_text:
            return None

        db_msg = MessageModel(
            empresa_id=empresa_id,
            conversation_id=conversation_id,
            role="agent",
            content=response_text,
            sender_name="AI Asistente",
        )
        self._session.add(db_msg)
        await self._session.flush()
        await self._repository.commit()

        return MessageResponse.model_validate(MessageDTO.model_validate(db_msg))

    async def _generate_response(
        self,
        *,
        last_user_msg: str,
        last_messages: list[str],
    ) -> str:
        history = " | ".join(last_messages[:-1]) if len(last_messages) > 1 else "Sin historial"

        if self._provider.is_configured:
            try:
                prompt = (
                    "Eres un asistente de ventas experto para una empresa de moda. "
                    "Responde al mensaje del cliente de forma natural, profesional y amable. "
                    "Usa el historial de la conversación para contextualizar tu respuesta.\n\n"
                    f"Historial: {history}\n"
                    f"Cliente: {last_user_msg}\n\n"
                    "Responde como un asesor de ventas:"
                )
                return await self._provider.generate(
                    system_prompt=prompt,
                    user_message=last_user_msg,
                    temperature=0.7,
                    max_tokens=200,
                )
            except Exception:
                logger.exception("OpenAI generation failed, falling back to templates")

        return await self._template_response(last_user_msg)

    async def _template_response(self, message: str) -> str:
        classification = await self._classifier.classify(message)
        intent = classification.intent.value

        templates = {
            "pricing": "¡Excelente pregunta! Permíteme darte los precios actualizados. ¿Hay algún producto en específico que te interese?",
            "purchase_intent": "¡Genial! Me encantaría ayudarte con tu compra. Dime el producto y talla que necesitas y lo procesamos.",
            "negotiation": "Entiendo que buscas la mejor opción. Podemos ofrecerte condiciones especiales. Dime qué producto te interesa.",
            "support": "Lamento el inconveniente. Cuéntame más detalles para poder ayudarte mejor.",
            "delivery": "Te ayudo a revisar el estado de tu pedido. ¿Podrías indicarme el número de seguimiento?",
            "greeting": "¡Hola! Bienvenido a nuestro servicio. ¿En qué puedo ayudarte el día de hoy? Estoy aquí para lo que necesites.",
            "product_question": "Con gusto te doy los detalles del producto. ¿Hay alguna característica específica que te interese conocer?",
            "sizing": "Claro, te ayudo con las tallas. Contamos con una guía detallada. ¿Qué producto te interesa?",
        }
        return templates.get(
            intent,
            "Gracias por tu mensaje. Permíteme consultar la información y te respondo a la brevedad. ¿Hay algo más en lo que pueda ayudarte?"
        )
