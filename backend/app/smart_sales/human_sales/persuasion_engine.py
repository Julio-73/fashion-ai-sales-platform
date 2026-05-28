import logging
from dataclasses import dataclass

logger = logging.getLogger("smart_sales.human_sales.persuasion")


REASSURANCE_PHRASES: list[str] = [
    "Es una excelente elección.",
    "Estás eligiendo calidad.",
    "No te vas a arrepentir.",
    "Es de lo mejor que tenemos.",
    "Vas a notar la diferencia.",
    "La calidad se nota al instante.",
    "Es una inversión que vale la pena.",
    "Estás comprando algo que realmente dura.",
]

CONFIDENCE_PHRASES: list[str] = [
    "Te queda perfecto, seguro.",
    "Confía, te va a encantar.",
    "Es justo lo que necesitas.",
    "Te lo recomiendo totalmente.",
    "No lo dudes, es para ti.",
]

PREMIUM_PERCEPTION_PHRASES: list[str] = [
    "La terminación es de primera calidad.",
    "Se nota el trabajo artesanal en cada detalle.",
    "Los materiales son seleccionados.",
    "Tiene un acabado que pocas prendas tienen.",
    "El diseño está pensado para quienes aprecian lo bueno.",
]

EMOTIONAL_PHRASES: list[str] = [
    "Imagínate lo bien que vas a verte.",
    "Te va a dar esa confianza que buscas.",
    "Vas a sentir la calidad al usarlo.",
    "Es de esas prendas que te hacen sentir bien.",
    "Te va a encantar cómo te queda.",
]


@dataclass
class PersuasionContext:
    reassurance: str = ""
    confidence: str = ""
    premium_perception: str = ""
    emotional: str = ""
    should_use: bool = False


_USED_PERSUASION: dict[str, dict[str, int]] = {}


class PersuasionEngine:
    def build_persuasion(self, conversation_id: str = "") -> PersuasionContext:
        import random

        context = PersuasionContext()

        used = _USED_PERSUASION.setdefault(conversation_id, {})

        _FIELD_MAP = {
            "reassurance": "reassurance",
            "confidence": "confidence",
            "premium": "premium_perception",
            "emotional": "emotional",
        }

        for key, pool in [
            ("reassurance", REASSURANCE_PHRASES),
            ("confidence", CONFIDENCE_PHRASES),
            ("premium", PREMIUM_PERCEPTION_PHRASES),
            ("emotional", EMOTIONAL_PHRASES),
        ]:
            idx = used.get(key, -1)
            available = [i for i in range(len(pool)) if i != idx]
            if available:
                new_idx = random.choice(available)
                used[key] = new_idx
                setattr(context, _FIELD_MAP[key], pool[new_idx])
            else:
                setattr(context, _FIELD_MAP[key], pool[0])

        context.should_use = True
        return context

    def reset(self, conversation_id: str) -> None:
        _USED_PERSUASION.pop(conversation_id, None)
