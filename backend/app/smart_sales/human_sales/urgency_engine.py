import logging
from dataclasses import dataclass

logger = logging.getLogger("smart_sales.human_sales.urgency")


URGENCY_PHRASES: list[tuple[str, float]] = [
    ("Si te gusta, no lo dejes pasar.", 0.5),
    ("Cuando se acaba, no sabemos cuándo vuelve.", 0.6),
    ("Es mejor asegurarlo ahora.", 0.5),
    ("No esperes demasiado o se agota.", 0.6),
    ("Está saliendo muy rápido, no te quedes sin él.", 0.7),
    ("Si te gusta, te recomiendo no esperar.", 0.5),
    ("Los que les gusta este estilo lo compran al instante.", 0.6),
    ("Apenas nos quedan, no va a durar.", 0.7),
]

USED_URGENCY: dict[str, set[int]] = {}


@dataclass
class UrgencyInfo:
    phrase: str = ""
    should_use: bool = False
    intensity: str = "none"


class UrgencyEngine:
    def evaluate(
        self,
        *,
        total_stock: int = 0,
        is_high_intent: bool = False,
        stage: str = "",
        conversation_id: str = "",
    ) -> UrgencyInfo:
        if stage not in ("persuasion", "closing", "upsell"):
            return UrgencyInfo()

        if total_stock <= 0:
            return UrgencyInfo()

        intensity = "none"

        if total_stock <= 3:
            intensity = "high"
        elif total_stock <= 10:
            intensity = "medium"
        elif is_high_intent:
            intensity = "low"
        else:
            return UrgencyInfo()

        pool = URGENCY_PHRASES

        used = USED_URGENCY.get(conversation_id, set())
        available = [i for i in range(len(pool)) if i not in used]

        if not available:
            available = list(range(len(pool)))
            used.clear()

        import random
        idx = random.choice(available)
        used.add(idx)
        USED_URGENCY[conversation_id] = used

        return UrgencyInfo(
            phrase=pool[idx][0],
            should_use=True,
            intensity=intensity,
        )

    def reset(self, conversation_id: str) -> None:
        USED_URGENCY.pop(conversation_id, None)
