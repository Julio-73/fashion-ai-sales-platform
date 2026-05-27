import logging

logger = logging.getLogger("ai_sales_agent.ai_live.handoff")


HANDOFF_KEYWORDS: dict[str, list[str]] = {
    "angry_customer": [
        "enojado", "molesto", "furioso", "queja", "pésimo", "terrible",
        "horrible", "indignado", "estafa", "decepcionado",
        "angry", "furious", "terrible", "scam", "disappointed",
    ],
    "refund_request": [
        "reembolso", "devolver dinero", "cancelar pedido", "quiero que me devuelvas",
        "refund", "money back", "cancel order", "give me my money",
    ],
    "complaint": [
        "producto defectuoso", "llegó roto", "no funciona", "talla incorrecta",
        "color diferente", "calidad baja", "no es lo que pedí",
        "defective", "broken", "wrong size", "wrong color", "poor quality",
    ],
    "negotiation_complex": [
        "descuento grande", "mitad de precio", "gratis", "no voy a pagar eso",
        "demasiado caro", "regalado",
        "half price", "free", "too expensive", "not paying that",
    ],
    "vip_customer": [
        "soy cliente frecuente", "siempre compro aquí", "vip", "cliente premium",
        "frecuente", "voy a dejar de comprar",
        "loyal customer", "always buy here", "premium client",
    ],
}


class HandoffService:
    async def evaluate_escalation(
        self,
        *,
        empresa_id,
        message: str,
        intent: str,
        lead_score: float,
    ) -> tuple[bool, str | None]:
        msg_lower = message.lower().strip()
        matched_triggers: list[str] = []

        for trigger, keywords in HANDOFF_KEYWORDS.items():
            for kw in keywords:
                if kw in msg_lower:
                    if trigger not in matched_triggers:
                        matched_triggers.append(trigger)
                    break

        if matched_triggers:
            reason = f"Escalado por: {', '.join(matched_triggers)}"
            logger.info(
                "Escalation triggered for empresa=%s: %s",
                empresa_id, reason,
            )
            return True, reason

        if intent == "return_request" or intent == "complaint":
            return True, f"Escalado por intent: {intent}"

        if lead_score >= 0.9:
            return True, "Escalado por lead_score alto"

        return False, None
