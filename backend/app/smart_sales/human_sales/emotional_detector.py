import re
from dataclasses import dataclass, field
from enum import Enum


class EmotionalState(str, Enum):
    excitement = "excitement"
    urgency = "urgency"
    indecision = "indecision"
    hesitation = "hesitation"
    frustration = "frustration"
    high_intent = "high_intent"
    greeting = "greeting"
    browsing = "browsing"
    neutral = "neutral"


@dataclass
class EmotionalResult:
    state: EmotionalState = EmotionalState.neutral
    confidence: float = 0.0
    secondary_states: list[EmotionalState] = field(default_factory=list)
    recommended_strategy: str = "inform"
    detected_keywords: list[str] = field(default_factory=list)


EXCITEMENT_PATTERNS: list[tuple[str, float]] = [
    (r"\b(?:quiero|necesito|dame|compra)\s+(?:eso|este|ese)\b", 0.9),
    (r"\b(?:me encanta|me fascina|me vuelve loco)\b", 0.9),
    (r"\b(?:increíble|espectacular|hermoso|precioso)\b", 0.7),
    (r"\b(?:es?\s+(?:brutal|cañón|fire|duro|top))\b", 0.8),
    (r"\b(?:lo quiero|la quiero|lo necesito|la necesito)\b", 0.95),
    (r"!!+", 0.5),
    (r"\b(?:perfecto|ideal|justo lo que)\b", 0.7),
]

URGENCY_PATTERNS: list[tuple[str, float]] = [
    (r"\b(?:urgente|ya|ahora mismo|inmediatamente|hoy mismo)\b", 0.9),
    (r"\b(?:necesito para|lo quiero para|para mañana|para hoy)\b", 0.85),
    (r"\b(?:cuanto antes|lo antes posible|rapido|rápido|pronto)\b", 0.8),
    (r"\b(?:última|último|últimas|últimos)\b", 0.6),
    (r"\b(?:ya voy|ya lo|ya la)\b", 0.5),
]

INDECISION_PATTERNS: list[tuple[str, float]] = [
    (r"\b(?:no sé|nose|no estoy seguro|no estoy segura)\b", 0.9),
    (r"\b(?:mmm|hmm|emm|a ver|déjame pensar)\b", 0.7),
    (r"\b(?:cual me recomiendas|qué me sugieres|tú qué crees)\b", 0.8),
    (r"\b(?:difícil decisión|no me decido|no sé cuál)\b", 0.85),
]

HESITATION_PATTERNS: list[tuple[str, float]] = [
    (r"\b(?:tal vez|quizás|quizá|capaz|a lo mejor|igual)\b", 0.7),
    (r"\b(?:pero es que|es que no sé|la verdad no)\b", 0.8),
    (r"\b(?:un poco caro|muy caro|mucho precio|no me alcanza)\b", 0.85),
    (r"\b(?:tengo que pensarlo|lo voy a pensar|lo consulto)\b", 0.9),
]

FRUSTRATION_PATTERNS: list[tuple[str, float]] = [
    (r"\b(?:no funciona|no sirve|no me gusta|no me sirve)\b", 0.9),
    (r"\b(?:qué mal|mal servicio|pésimo|terrible)\b", 0.8),
    (r"\b(?:nunca me llega|no llega|no aparece|error)\b", 0.85),
    (r"\b(?:devolver|reclamo|queja|devolución)\b", 0.7),
    (r"\b(?:enfadado|molesto|enojado|disgustado)\b", 0.9),
]

HIGH_INTENT_PATTERNS: list[tuple[str, float]] = [
    (r"\b(?:me lo llevo|me la llevo|lo compro|la compro)\b", 0.95),
    (r"\b(?:quiero comprar|deseo comprar|voy a comprar)\b", 0.9),
    (r"\b(?:cómo lo pido|cómo lo compro|lo quiero ya)\b", 0.85),
    (r"\b(?:separar|apartar|reservar)\b", 0.8),
    (r"\b(?:talla\s+\w+|color\s+\w+)\s+(?:tienes|hay|manejan)\b", 0.7),
]

GREETING_PATTERNS: list[tuple[str, float]] = [
    (r"\b(?:hola|buenas|buen día|buenas tardes|buenos días|hey|oye|buenass)\b", 0.9),
    (r"\b(?:qué tal|qué hay|cómo estás|como estas|q tal)\b", 0.8),
    (r"^(?:hola|buenas|hey|oye)\b", 0.95),
]

BROWSING_PATTERNS: list[tuple[str, float]] = [
    (r"\b(?:qué tienes|qué hay|muéstrame|enséñame|ver)\b", 0.7),
    (r"\b(?:catálogo|productos|ropa|modelos)\b", 0.6),
    (r"\b(?:busco|ando buscando|estoy viendo|estoy mirando)\b", 0.7),
    (r"\b(?:solo viendo|solo mirando|nada más ver)\b", 0.8),
]


def _score_patterns(text: str, patterns: list[tuple[str, float]]) -> list[tuple[str, float]]:
    results: list[tuple[str, float]] = []
    for pattern, score in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            results.append((match.group(), score))
    return results


class EmotionalDetector:
    def detect(self, text: str) -> EmotionalResult:
        if not text or not text.strip():
            return EmotionalResult()

        results: dict[EmotionalState, list[tuple[str, float]]] = {}

        for state, patterns in [
            (EmotionalState.excitement, EXCITEMENT_PATTERNS),
            (EmotionalState.urgency, URGENCY_PATTERNS),
            (EmotionalState.indecision, INDECISION_PATTERNS),
            (EmotionalState.hesitation, HESITATION_PATTERNS),
            (EmotionalState.frustration, FRUSTRATION_PATTERNS),
            (EmotionalState.high_intent, HIGH_INTENT_PATTERNS),
            (EmotionalState.greeting, GREETING_PATTERNS),
            (EmotionalState.browsing, BROWSING_PATTERNS),
        ]:
            matches = _score_patterns(text, patterns)
            if matches:
                results[state] = matches

        if not results:
            return EmotionalResult()

        best_state = max(results, key=lambda s: max(r[1] for r in results[s]))
        best_confidence = max(r[1] for r in results[best_state])

        all_keywords = []
        for matches in results.values():
            all_keywords.extend(m[0] for m in matches)

        secondary = [s for s in results if s != best_state]

        strategy = _map_strategy(best_state, best_confidence)

        return EmotionalResult(
            state=best_state,
            confidence=best_confidence,
            secondary_states=secondary,
            recommended_strategy=strategy,
            detected_keywords=all_keywords,
        )


def _map_strategy(state: EmotionalState, confidence: float) -> str:
    mapping = {
        EmotionalState.excitement: "reinforce_and_close",
        EmotionalState.urgency: "urgency_close",
        EmotionalState.indecision: "help_decide",
        EmotionalState.hesitation: "reassure_and_support",
        EmotionalState.frustration: "deescalate_and_solve",
        EmotionalState.high_intent: "direct_close",
        EmotionalState.greeting: "warm_greeting",
        EmotionalState.browsing: "explore_and_recommend",
        EmotionalState.neutral: "inform",
    }
    return mapping.get(state, "inform")
