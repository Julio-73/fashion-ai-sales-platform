import re
from enum import Enum
from dataclasses import dataclass, field


class ConversationalIntent(str, Enum):
    greeting = "greeting"
    gratitude = "gratitude"
    farewell = "farewell"
    casual_chat = "casual_chat"
    hesitation = "hesitation"
    confusion = "confusion"
    browsing = "browsing"
    interested = "interested"
    committed = "committed"
    ready_to_buy = "ready_to_buy"
    objection = "objection"
    sizing = "sizing"
    styling = "styling"
    comparison = "comparison"
    unknown = "unknown"


@dataclass
class IntentResult:
    intent: ConversationalIntent = ConversationalIntent.unknown
    confidence: float = 0.0
    secondary_intents: list[ConversationalIntent] = field(default_factory=list)
    triggered_patterns: list[str] = field(default_factory=list)
    detected_entities: dict[str, str] = field(default_factory=dict)


SHORT_WORDS: set[str] = {
    "hola", "holi", "holis", "hello", "hi", "hey", "heey", "buenas",
    "gracias", "grax", "thanks", "thank", "ok", "okay", "okei", "dale",
    "listo", "perfecto", "genial", "excelente", "sale", "simon", "si",
    "no", "nop", "nope", "mmm", "hmm", "emm", "ah", "ahh", "wow",
    "wuuu", "oha", "oye", "ey", "byee", "chao", "chau", "adiós", "adios",
    "bye", "bai", "nos vemos",
}


PATTERNS: list[tuple[str, ConversationalIntent, float]] = [
    # greeting
    (r"^(?:hola|holi|holis|hello|hi|hey|heey)\b", ConversationalIntent.greeting, 0.95),
    (r"^(?:buenas|buen[oad]s|qu[eé] tal|qu[eé] hay|q tal)\b", ConversationalIntent.greeting, 0.9),
    (r"\b(?:bienvenido|bienvenida)\b", ConversationalIntent.greeting, 0.8),

    # gratitude
    (r"\b(?:gracias|thank|thanks|grax|mil gracias|muchas gracias|te agradezco)\b", ConversationalIntent.gratitude, 0.95),
    (r"\b(?:agradecid[oa]|se agradece)\b", ConversationalIntent.gratitude, 0.8),

    # hesitation
    (r"^(?:mmm|hmm|emm|mm)\b", ConversationalIntent.hesitation, 0.9),
    (r"\b(?:no sé|nose|no estoy segur[oa]|tal vez|quiz[áa]|a lo mejor|capaz)\b", ConversationalIntent.hesitation, 0.8),
    (r"\b(?:lo pensar[eé]|lo voy a pensar|lo consulto|d[eé]jame pensar)\b", ConversationalIntent.hesitation, 0.85),
    (r"\b(?:luego vuelvo|despu[eé]s te escribo|ahorita veo)\b", ConversationalIntent.hesitation, 0.8),

    # farewell (new)
    (r"\b(?:eso es todo|es todo|n[aá]da m[aá]s|eso ser[ií]a todo)\b", ConversationalIntent.farewell, 0.95),
    (r"^(?:chao|chau|adi[oó]s|adios|bye|bai|nos vemos|hasta luego|hasta pronto)\b", ConversationalIntent.farewell, 0.95),
    (r"\b(?:gracias\s+(?:por\s+tu\s+ayuda|por\s+todo|igual|de todas formas))\b", ConversationalIntent.farewell, 0.85),
    (r"\b(?:ya me voy|me retiro|gracias por\s+tu\s+tiempo)\b", ConversationalIntent.farewell, 0.85),

    # casual chat
    (r"^(?:ok|okay|okei|dale|listo|perfecto)\b", ConversationalIntent.casual_chat, 0.8),
    (r"^(?:genial|excelente|s[uú]per|bacan|ch[eé]vere|wow)\b", ConversationalIntent.casual_chat, 0.8),
    (r"^(?:sale|simon|si|ya|ah ya|ahh|enta)\b", ConversationalIntent.casual_chat, 0.7),
    (r"^(?:entiendo|comprendo|claro|oka)\b", ConversationalIntent.casual_chat, 0.7),
    (r"\b(?:c[oó]mo est[aá]s|c[oó]mo te va|c[oó]mo andas|todo bien|qu[eé] tal tu d[ií]a)\b", ConversationalIntent.casual_chat, 0.9),
    (r"\b(?:un gust[oa]|encantad[oa]|mucho gust[oa])\b", ConversationalIntent.casual_chat, 0.8),
    (r"\b(?:gracias a ti|a ti gracias|igual gracias)\b", ConversationalIntent.gratitude, 0.85),

    # confusion
    (r"\b(?:c[oó]mo|c[oó]mo así|no entiendo|no comprendo|explica)\b", ConversationalIntent.confusion, 0.8),
    (r"\b(?:qu[eé] significa|qu[eé] es|no me queda claro)\b", ConversationalIntent.confusion, 0.7),

    # objection
    (r"\b(?:car[oa]|car[ií]simo|costoso|elevado|precio)\b", ConversationalIntent.objection, 0.7),
    (r"\b(?:muy caro|muy cara|demasiado|no me alcanza)\b", ConversationalIntent.objection, 0.8),
    (r"\b(?:otra opci[oó]n|alternativa|algo m[aá]s barato|m[aá]s econ[oó]mico)\b", ConversationalIntent.objection, 0.8),

    # sizing
    (r"\b(?:talla|talle|tayo|size)\s*[:\s]?[a-zA-Z0-9]\b", ConversationalIntent.sizing, 0.9),
    (r"(?:tienes|hay|manejan|consigues)\s*(?:en|la|talla)\s+\w", ConversationalIntent.sizing, 0.85),
    (r"\b(?:talla s|talla m|talla l|talla xl|talla xxl|small|medium|large)\b", ConversationalIntent.sizing, 0.95),
    (r"\b(?:me qued[aá]|cu[aá]l es mi talla|qu[eé] talla)\b", ConversationalIntent.sizing, 0.8),

    # styling
    (r"\b(?:combina|queda|qu[eé] combina|qu[eé] queda|outfit)\b", ConversationalIntent.styling, 0.8),
    (r"\b(?:c[oó]mo lo uso|c[oó]mo combinarlo|con qu[eé])\b", ConversationalIntent.styling, 0.85),
    (r"\b(?:estilo|look|outfit completo|armar|sugiere)\b", ConversationalIntent.styling, 0.7),

    # comparison
    (r"\b(?:cu[aá]l es mejor|cu[aá]l recomiendas|diferencia|comparar)\b", ConversationalIntent.comparison, 0.8),
    (r"\b(?:vs|versus|o este|o esta)\b", ConversationalIntent.comparison, 0.6),

    # browsing
    (r"\b(?:qu[eé] tienes|qu[eé] hay|mu[eé]strame|enseñame|ver)\b", ConversationalIntent.browsing, 0.8),
    (r"\b(?:cat[aá]logo|productos|modelos|ropa|qu[eé] venden)\b", ConversationalIntent.browsing, 0.7),
    (r"\b(?:busco|ando buscando|estoy viendo|estoy mirando|quiero ver)\b", ConversationalIntent.browsing, 0.7),
    (r"\b(?:sugiere|recomi[eé]ndame|qu[eé] me recomiendas)\b", ConversationalIntent.browsing, 0.8),

    # interested
    (r"\b(?:me gusta|me interesa|se ve bien|se ve bueno|me llama)\b", ConversationalIntent.interested, 0.7),
    (r"\b(?:cu[eé]ntame|dime m[aá]s|c[oó]mo es|c[oó]mo se ve)\b", ConversationalIntent.interested, 0.6),

    # committed
    (r"\b(?:quiero es[eoas]|lo quiero|la quiero|me lo llevo|me la llevo)\b", ConversationalIntent.committed, 0.85),
    (r"\b(?:ese modelo|esa pieza|esa prenda|ese producto)\b", ConversationalIntent.committed, 0.7),

    # ready_to_buy
    (r"\b(?:lo compro|la compro|comprar|dame|separar|apartar|reservar)\b", ConversationalIntent.ready_to_buy, 0.85),
    (r"\b(?:c[oó]mo lo pido|c[oó]mo lo compro|lo quiero ya|ya lo quiero)\b", ConversationalIntent.ready_to_buy, 0.8),
    (r"\b(?:delivery|env[ií]o|cu[aá]nto demora|cu[aá]nto cuesta)\b", ConversationalIntent.ready_to_buy, 0.6),
]


class ConversationalIntentDetector:
    def detect(self, message: str) -> IntentResult:
        msg = message.strip()
        if not msg:
            return IntentResult()

        msg_lower = msg.lower().strip()
        result = IntentResult()
        found: list[tuple[ConversationalIntent, float, str]] = []

        for pattern, intent, confidence in PATTERNS:
            match = re.search(pattern, msg_lower)
            if match:
                found.append((intent, confidence, match.group()))

        if not found:
            if msg_lower in SHORT_WORDS:
                for intent in (ConversationalIntent.greeting, ConversationalIntent.gratitude,
                               ConversationalIntent.casual_chat, ConversationalIntent.hesitation):
                    for pattern, iobj, conf in PATTERNS:
                        if iobj == intent and re.match(pattern, msg_lower):
                            found.append((intent, conf, msg_lower))

        if not found:
            return IntentResult()

        seen_intents: set[ConversationalIntent] = set()
        best: tuple[ConversationalIntent, float, str] | None = None

        for intent, conf, trigger in found:
            if intent not in seen_intents:
                seen_intents.add(intent)
            if best is None or conf > best[1]:
                best = (intent, conf, trigger)

        if best is None:
            return IntentResult()

        result.intent = best[0]
        result.confidence = best[1]
        result.triggered_patterns = [best[2]]
        result.secondary_intents = [s for s in seen_intents if s != best[0]]

        size_m = re.search(r"talla\s*[:\s]?\s*([a-zA-Z0-9]+)", msg_lower)
        if size_m:
            result.detected_entities["size"] = size_m.group(1)

        color_m = re.search(r"color\s*[:\s]?\s*(\w+)", msg_lower)
        if color_m:
            result.detected_entities["color"] = color_m.group(1)

        return result
