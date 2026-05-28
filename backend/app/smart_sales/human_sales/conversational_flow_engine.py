from dataclasses import dataclass, field
from enum import Enum


class SalesStage(str, Enum):
    greeting = "greeting"
    discovery = "discovery"
    recommendation = "recommendation"
    persuasion = "persuasion"
    closing = "closing"
    upsell = "upsell"
    retention = "retention"
    completed = "completed"


STAGE_TRANSITIONS: dict[SalesStage, list[SalesStage]] = {
    SalesStage.greeting: [SalesStage.discovery, SalesStage.recommendation],
    SalesStage.discovery: [SalesStage.recommendation, SalesStage.persuasion],
    SalesStage.recommendation: [SalesStage.persuasion, SalesStage.closing, SalesStage.discovery],
    SalesStage.persuasion: [SalesStage.closing, SalesStage.upsell, SalesStage.recommendation],
    SalesStage.closing: [SalesStage.upsell, SalesStage.retention, SalesStage.completed],
    SalesStage.upsell: [SalesStage.closing, SalesStage.retention, SalesStage.completed],
    SalesStage.retention: [SalesStage.completed, SalesStage.recommendation],
    SalesStage.completed: [SalesStage.greeting],
}


@dataclass
class FlowContext:
    stage: SalesStage = SalesStage.greeting
    previous_stage: SalesStage | None = None
    stage_history: list[SalesStage] = field(default_factory=list)
    message_count_in_stage: int = 0
    total_messages: int = 0
    last_product_type: str | None = None
    last_size: str | None = None
    last_color: str | None = None
    last_style: str | None = None
    last_occasion: str | None = None
    last_gender: str | None = None
    closing_initiated: bool = False
    upsell_offered: bool = False
    product_shared: str | None = None


TRANSITION_KEYWORDS: dict[SalesStage, list[str]] = {
    SalesStage.greeting: [],
    SalesStage.discovery: [
        "quiero", "busco", "necesito", "recomiendame", "qué tienes",
        "muéstrame", "enséñame", "ver", "comprar",
        "me gusta", "me interesa", "se ve", "buena opción",
        "cuéntame", "dime más", "cómo es",
    ],
    SalesStage.recommendation: [
        "me gusta", "lo quiero", "la quiero", "me lo llevo",
        "buena elección", "dale", "voy por ese",
    ],
    SalesStage.persuasion: [
        "me convence", "está bien", "ok", "lo compro",
        "lo quiero", "talla", "cuanto cuesta",
    ],
    SalesStage.closing: [
        "comprar", "pagar", "ordenar", "pedido",
        "delivery", "envío", "separar", "apartar",
    ],
    SalesStage.upsell: [
        "no", "solo eso", "ok", "sí", "también",
    ],
}


def detect_stage_from_message(
    message: str,
    current_stage: SalesStage,
    emotional_state: str | None = None,
) -> SalesStage:
    msg_lower = message.lower().strip()

    if emotional_state in ("high_intent", "excitement") \
       and current_stage in (SalesStage.discovery, SalesStage.recommendation, SalesStage.persuasion):
        return SalesStage.closing

    if emotional_state == "greeting" and current_stage == SalesStage.greeting:
        return SalesStage.discovery

    GREETING_WORDS = ["hola", "buenas", "buen día", "buenos días", "buenas tardes", "hey", "oye"]
    if current_stage == SalesStage.greeting:
        for gw in GREETING_WORDS:
            if gw in msg_lower:
                return SalesStage.discovery

    for stage, keywords in TRANSITION_KEYWORDS.items():
        if stage == SalesStage.greeting and current_stage != SalesStage.greeting:
            continue
        for kw in keywords:
            if kw in msg_lower:
                if stage == SalesStage.closing and current_stage == SalesStage.greeting:
                    continue
                return stage

    return current_stage


class ConversationalFlowEngine:
    def __init__(self) -> None:
        self._contexts: dict[str, FlowContext] = {}

    def get_or_create(self, conversation_id: str) -> FlowContext:
        if conversation_id not in self._contexts:
            self._contexts[conversation_id] = FlowContext()
        return self._contexts[conversation_id]

    def update_stage(
        self,
        conversation_id: str,
        message: str,
        emotional_state: str | None = None,
    ) -> SalesStage:
        ctx = self.get_or_create(conversation_id)
        ctx.total_messages += 1

        new_stage = detect_stage_from_message(message, ctx.stage, emotional_state)

        if new_stage != ctx.stage:
            ctx.previous_stage = ctx.stage
            ctx.stage_history.append(ctx.stage)
            ctx.stage = new_stage
            ctx.message_count_in_stage = 0
        else:
            ctx.message_count_in_stage += 1

        return ctx.stage

    def get_flow_context(self, conversation_id: str) -> FlowContext | None:
        return self._contexts.get(conversation_id)

    def should_persuade(self, conversation_id: str) -> bool:
        ctx = self.get_or_create(conversation_id)
        return ctx.stage in (SalesStage.persuasion, SalesStage.closing)

    def should_push_closing(self, conversation_id: str) -> bool:
        ctx = self.get_or_create(conversation_id)
        return ctx.stage == SalesStage.closing and not ctx.closing_initiated

    def mark_closing_initiated(self, conversation_id: str) -> None:
        ctx = self.get_or_create(conversation_id)
        ctx.closing_initiated = True

    def should_upsell(self, conversation_id: str) -> bool:
        ctx = self.get_or_create(conversation_id)
        return ctx.stage in (SalesStage.closing, SalesStage.upsell) and not ctx.upsell_offered

    def mark_upsell_offered(self, conversation_id: str) -> None:
        ctx = self.get_or_create(conversation_id)
        ctx.upsell_offered = True

    def get_stage_prompt(self, stage: SalesStage) -> str:
        prompts = {
            SalesStage.greeting: (
                "Saluda al cliente de forma cálida y pregúntale qué está buscando."
            ),
            SalesStage.discovery: (
                "Haz preguntas para entender mejor lo que busca el cliente: "
                "estilo, ocasión, color, talla."
            ),
            SalesStage.recommendation: (
                "Recomienda productos específicos con descripciones atractivas. "
                "Usa emojis y lenguaje persuasivo."
            ),
            SalesStage.persuasion: (
                "Refuerza la decisión del cliente. Usa pruebas sociales, "
                "escasez o urgencia si aplica. Sé persuasivo sin ser agresivo."
            ),
            SalesStage.closing: (
                "El cliente está listo para comprar. Pregunta talla, confirma "
                "producto, y guíalo al cierre de la venta."
            ),
            SalesStage.upsell: (
                "Sugiere un producto complementario. Sé natural, no fuerces. "
                "Si rechaza, respeta y cierra."
            ),
            SalesStage.retention: (
                "Agradece al cliente, confirma el pedido y ofrece ayuda futura."
            ),
            SalesStage.completed: (
                "Conversación completada. Pregunta si necesita algo más."
            ),
        }
        return prompts.get(stage, "Responde de forma natural y útil.")
