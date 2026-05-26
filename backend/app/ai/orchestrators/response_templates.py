import logging
from typing import ClassVar

from app.ai.schemas.ai_schemas import IntentType, ReplyType

logger = logging.getLogger("ai_sales_agent.ai.orchestrator")

SALES_TEMPLATES: dict[IntentType, str] = {
    IntentType.greeting: (
        "¡Hola! 👋 Soy el asistente virtual de ventas. ¿En qué puedo ayudarte hoy? "
        "Estoy aquí para mostrarte nuestra colección y responder tus preguntas."
    ),
    IntentType.pricing: (
        "Gracias por tu interés. Te comparto la información de precios de nuestros productos. "
        "¿Te gustaría ver algún artículo en particular?"
    ),
    IntentType.purchase_intent: (
        "Excelente elección. Me encantaría ayudarte con tu compra. "
        "¿Prefieres que te ayude a realizar el pedido ahora o necesitas más información?"
    ),
    IntentType.negotiation: (
        "Entiendo que estás buscando la mejor oferta. Déjame ver qué opciones "
        "podemos ofrecerte para que tengas el mejor precio posible."
    ),
    IntentType.delivery: (
        "Claro, te explico nuestra política de envíos. Trabajamos con entregas "
        "rápidas y seguras. ¿Podrías decirme tu código postal para darte "
        "información más precisa?"
    ),
    IntentType.product_question: (
        "Con gusto te proporciono los detalles del producto que te interesa. "
        "¿Hay alguna característica específica sobre la que quieras saber más?"
    ),
    IntentType.sizing: (
        "Claro, te ayudo con las tallas. Contamos con una guía detallada "
        "para que encuentres la talla perfecta. ¿Podrías indicarme qué "
        "producto te interesa?"
    ),
    IntentType.support: (
        "Lamento que tengas un inconveniente. Estoy aquí para ayudarte. "
        "¿Podrías contarme más detalles para poder asistirte de la mejor manera?"
    ),
    IntentType.return_request: (
        "Entiendo que deseas gestionar una devolución. Te conectamos con "
        "nuestro equipo de soporte especializado para que te ayuden."
    ),
}

SUPPORT_TEMPLATES: dict[IntentType, str] = {
    IntentType.support: (
        "He identificado que necesitas asistencia. Voy a escalar tu caso "
        "a nuestro equipo de soporte para que te atiendan personalmente."
    ),
    IntentType.return_request: (
        "Tu solicitud de devolución ha sido recibida. Un agente de soporte "
        "te contactará en breve para procesarla."
    ),
}


class ResponseTemplateBuilder:
    ESCALATION_NOTICE: ClassVar[str] = (
        "Tu consulta ha sido derivada a un agente humano "
        "que te atenderá personalmente."
    )
    FOLLOW_UP_TEMPLATE: ClassVar[str] = (
        "Hola {customer_name}, quería darle seguimiento a nuestra "
        "conversación anterior. ¿Has tenido oportunidad de pensar en "
        "los productos que te mostré? Quedo atento a cualquier pregunta."
    )
    CROSS_SELL_TEMPLATE: ClassVar[str] = (
        "Me alegra que te haya interesado. También tenemos otros productos "
        "que podrían complementar tu elección. ¿Te gustaría conocerlos?"
    )

    @classmethod
    def build_sales_response(cls, intent: IntentType) -> str:
        return SALES_TEMPLATES.get(intent, "")

    @classmethod
    def build_support_response(cls, intent: IntentType) -> str:
        return SUPPORT_TEMPLATES.get(intent, "")

    @classmethod
    def build_follow_up(cls, customer_name: str = "") -> str:
        return cls.FOLLOW_UP_TEMPLATE.format(customer_name=customer_name or "cliente")

    @classmethod
    def build_cross_sell(cls) -> str:
        return cls.CROSS_SELL_TEMPLATE

    @classmethod
    def get_reply_type(cls, intent: IntentType) -> ReplyType:
        if intent == IntentType.support:
            return ReplyType.support
        if intent == IntentType.return_request:
            return ReplyType.escalation
        if intent == IntentType.greeting:
            return ReplyType.greeting
        if intent in (IntentType.purchase_intent, IntentType.pricing,
                       IntentType.negotiation, IntentType.product_question,
                       IntentType.sizing, IntentType.delivery):
            return ReplyType.sales
        return ReplyType.no_reply
