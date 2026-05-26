"""Rule-based intent classifier for sales messages.

Detects commercial intent using keyword patterns.
Extensible via IntentRule registry — no AI required.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.sales.intents.intent import IntentType


@dataclass(frozen=True)
class IntentRule:
    intent: IntentType
    patterns: list[str] = field(default_factory=list)
    weight: int = 0

    def matches(self, text: str, /) -> bool:
        lower = text.lower().strip()
        for pattern in self.patterns:
            if re.search(pattern, lower):
                return True
        return False


_DEFAULT_RULES: list[IntentRule] = [
    IntentRule(
        intent=IntentType.greeting,
        patterns=[r"^\s*(hola|buenas|buen[asod]{2,3}|hey|saludos|qu[eé] tal)\b"],
    ),
    IntentRule(
        intent=IntentType.pricing_intent,
        patterns=[
            r"\b(precios?|cu[eé]nto|cost[oó]|val[oó]r|tarifa|cu[aá]l es el precio|cuesta)\b",
            r"\b(price?|how much|costo)\b",
        ],
    ),
    IntentRule(
        intent=IntentType.purchase_intent,
        patterns=[
            r"\b(quiero\s*comprar|compr[oa]r|adquirir|ordenar|pedir|lo quiero|me llevo|reservar|apartar)\b",
            r"\b(compr[oa]r[a-z]*\s+ahora|pagar|facturar|checkout|cash|efectivo|transferencia|yappy|plin)\b",
        ],
    ),
    IntentRule(
        intent=IntentType.negotiation_intent,
        patterns=[
            r"\b(descuent[o0]|rebaj[ao]|oferta|promoci[oó]n|m[aá]s barato|precio especial|menos precio|negociar)\b",
            r"\b(discount|cheaper|deal|bargain|precio\s*mayo(rista|reo))\b",
        ],
    ),
    IntentRule(
        intent=IntentType.shipping_intent,
        patterns=[
            r"\b(delivery|env[ií]o|env[ií]an|despacho|env[ií]en|llegad[ao]|reparto|domicilio|courier|shipping)\b",
            r"\b(c[uú]anto\s*(tarda|llega)|tiempo\s*de\s*entrega|d[ií]as\s*de\s*entrega)\b",
        ],
    ),
    IntentRule(
        intent=IntentType.support_intent,
        patterns=[
            r"\b(ayuda|soporte|problema|error|fall[ao]|no funciona|asistencia|reclamo|devoluci[oó]n|cambio|garant[ií]a)\b",
            r"\b(no me gust[oó]|no sirve|dañad[ao]|roto|help|support|issue)\b",
        ],
    ),
    IntentRule(
        intent=IntentType.product_interest,
        patterns=[
            r"\b(tienes?|hay|mu[eé]strame|enseñame|quisiera\s*ver|me\s*interesa|cat[aá]logo|colecci[oó]n)\b",
            r"\b(modelo|talla|colores?|disponible|stock|variante|sku)\b",
        ],
    ),
]


class IntentClassifier:
    def __init__(self, rules: list[IntentRule] | None = None) -> None:
        self._rules = rules or _DEFAULT_RULES

    def classify(self, message: str, /) -> tuple[IntentType, int]:
        for rule in self._rules:
            if rule.matches(message):
                return rule.intent, rule.weight
        return IntentType.unknown, 0

    def classify_all(self, message: str, /) -> list[tuple[IntentType, int]]:
        results: list[tuple[IntentType, int]] = []
        seen: set[IntentType] = set()
        for rule in self._rules:
            if rule.matches(message) and rule.intent not in seen:
                results.append((rule.intent, rule.weight))
                seen.add(rule.intent)
        return results
