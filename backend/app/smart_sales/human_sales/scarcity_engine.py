import logging
from dataclasses import dataclass

logger = logging.getLogger("smart_sales.human_sales.scarcity")


LOW_STOCK_PHRASES: list[str] = [
    "Nos quedan pocas unidades.",
    "El stock está volando.",
    "Ya casi no queda.",
    "Se está agotando rápido.",
    "Quedan muy pocas.",
]

MEDIUM_STOCK_PHRASES: list[str] = [
    "El stock está bajando.",
    "Se está vendiendo bastante.",
    "Solo quedan algunas unidades.",
]

HIGH_DEMAND_PHRASES: list[str] = [
    "Está teniendo mucha salida.",
    "Es uno de los más buscados.",
    "La demanda está altísima.",
]

SEASONAL_PHRASES: list[str] = [
    "Es la prenda de la temporada.",
    "Perfecto para esta época.",
    "Está en su mejor momento.",
]

USED_SCARCITY: dict[str, set[int]] = {}


@dataclass
class ScarcityInfo:
    phrase: str = ""
    should_use: bool = False
    intensity: str = "none"


class ScarcityEngine:
    def evaluate(
        self,
        *,
        total_stock: int = 0,
        is_high_demand: bool = False,
        is_seasonal: bool = False,
        conversation_id: str = "",
    ) -> ScarcityInfo:
        if total_stock <= 0:
            return ScarcityInfo()

        if total_stock <= 3 and total_stock > 0:
            pool = LOW_STOCK_PHRASES
            intensity = "high"
        elif total_stock <= 10:
            pool = LOW_STOCK_PHRASES + MEDIUM_STOCK_PHRASES
            intensity = "medium"
        elif is_high_demand:
            pool = HIGH_DEMAND_PHRASES
            intensity = "medium"
        elif is_seasonal:
            pool = SEASONAL_PHRASES
            intensity = "low"
        else:
            return ScarcityInfo()

        used = USED_SCARCITY.get(conversation_id, set())
        available = [i for i in range(len(pool)) if i not in used]

        if not available:
            available = list(range(len(pool)))
            used.clear()

        import random
        idx = random.choice(available)
        used.add(idx)
        USED_SCARCITY[conversation_id] = used

        return ScarcityInfo(
            phrase=pool[idx],
            should_use=True,
            intensity=intensity,
        )

    def reset(self, conversation_id: str) -> None:
        USED_SCARCITY.pop(conversation_id, None)
