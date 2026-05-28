import random
from dataclasses import dataclass


@dataclass
class ToneProfile:
    name: str
    emojis: list[str]
    openings: list[str]
    closings: list[str]
    adjectives: list[str]
    connectors: list[str]
    style_adjectives: dict[str, str]
    writing_style: str


STREETWEAR = ToneProfile(
    name="streetwear",
    emojis=["🔥", "💯", "👟", "🧢", "🆒", "👊", "⚡", "🎯"],
    openings=[
        "¡Buenísima esa elección!",
        "Esa pieza está brutal.",
        "Qué buen ojo tienes.",
        "Eso está cañón.",
        "Te va a quedar mortal.",
    ],
    closings=[
        "¿Te lo separo?",
        "Dime talla y te lo aparto.",
        "Pídelo antes de que vuele.",
        "¿Cuál te gusta más?",
        "Te ayudo con la talla.",
    ],
    adjectives=["brutal", "cañón", "fresh", "duro", "mortal", "top", "cómodo", "clean"],
    connectors=["y", "además", "también", "por cierto"],
    style_adjectives={
        "pantalon": "relajado",
        "camiseta": "oversize",
        "zapatillas": "fresh",
        "chaqueta": "statement",
        "gorra": "complemento",
    },
    writing_style="urban_casual",
)

LUXURY = ToneProfile(
    name="luxury",
    emojis=["✨", "🌟", "💎", "👔", "👗", "🎩", "⭐", "💫"],
    openings=[
        "Excelente elección.",
        "Un acierto total.",
        "Muy buena selección.",
        "Elegancia pura.",
        "Distinción absoluta.",
    ],
    closings=[
        "¿Prefiere que se lo reservemos?",
        "Queda a su disposición.",
        "¿Se lo preparamos?",
        "Estaremos encantados de asistirle.",
        "¿Algo más que pueda añadir?",
    ],
    adjectives=[
        "elegante", "premium", "exclusivo", "sofisticado",
        "distinguido", "selecto", "impecable", "refinado",
    ],
    connectors=[
        "asimismo", "además", "cabe destacar",
        "por otra parte", "igualmente",
    ],
    style_adjectives={
        "pantalon": "de corte impecable",
        "camisa": "de alta costura",
        "americana": "sastrería italiana",
        "traje": "hecho a medida",
        "zapato": "de piel genuina",
    },
    writing_style="formal_refined",
)

PREMIUM = ToneProfile(
    name="premium",
    emojis=["✨", "🎯", "💫", "👔", "👗", "⭐", "✅", "🌟"],
    openings=[
        "Buena elección.",
        "Me encanta tu estilo.",
        "Muy buen gusto.",
        "Esa pieza es increíble.",
        "Te va a encantar.",
    ],
    closings=[
        "¿Te lo aparto?",
        "¿Cuál te parece mejor?",
        "¿Te ayudo con la talla?",
        "Dime y te lo reservo.",
        "¿Alguna duda sobre el modelo?",
    ],
    adjectives=[
        "increíble", "espectacular", "premium", "cómodo",
        "versátil", "moderno", "elegante", "top",
    ],
    connectors=["y", "además", "también", "por otro lado", "incluso"],
    style_adjectives={
        "pantalon": "de corte moderno",
        "camisa": "de tejido premium",
        "chaqueta": "con acabado de lujo",
        "vestido": "con caída perfecta",
        "blazer": "de sastrería fina",
    },
    writing_style="modern_premium",
)

CASUAL = ToneProfile(
    name="casual",
    emojis=["😊", "👌", "🔥", "💪", "✨", "👍", "😎", "👀"],
    openings=[
        "¡Qué buena onda tu elección!",
        "Eso se ve muy chévere.",
        "Me encanta lo que buscas.",
        "Esa es una gran opción.",
        "Qué bien, excelente gusto.",
    ],
    closings=[
        "¿Te parece bien alguna?",
        "¿Cuál te gusta?",
        "Te ayudo a decidir.",
        "¿Qué te parece?",
        "¿Vamos con esa?",
    ],
    adjectives=[
        "chévere", "bacán", "cómodo", "lindo",
        "bonito", "súper", "genial", "divertido",
    ],
    connectors=["y", "además", "también", "por cierto", "oye"],
    style_adjectives={
        "pantalon": "cómodo",
        "camiseta": "básica pero con estilo",
        "zapatillas": "súper cómodas",
        "jean": "de uso diario",
        "casaca": "para el día a día",
    },
    writing_style="friendly_casual",
)

MODERN_FASHION = ToneProfile(
    name="modern_fashion",
    emojis=["🔥", "⭐", "✅", "👀", "🛒", "🎯", "💫", "👌"],
    openings=[
        "Ideal para lo que buscas.",
        "Perfecta selección.",
        "Justo lo que necesitas.",
        "Muy buena opción.",
        "Excelente elección.",
    ],
    closings=[
        "¿Te interesa alguno?",
        "¿Te lo llevas?",
        "¿Lo agregamos?",
        "¿Cuál prefieres?",
        "¿Te ayudo con el pedido?",
    ],
    adjectives=[
        "ideal", "perfecto", "moderno", "versátil",
        "funcional", "tendencia", "actual", "práctico",
    ],
    connectors=["además", "también", "por otro lado", "igualmente", "así que"],
    style_adjectives={
        "pantalon": "moderno",
        "camisa": "de última tendencia",
        "vestido": "contemporáneo",
        "chaqueta": "actual",
        "accesorio": "trendy",
    },
    writing_style="neutral_modern",
)

GENZ_FASHION = ToneProfile(
    name="genz_fashion",
    emojis=["🔥", "✨", "💅", "👀", "no cap", "fr", "slay", "😳"],
    openings=[
        "OMG esa elección.",
        "Literalmente perfecto.",
        "Eso es un vibe total.",
        "Te va a quedar slay.",
        "Eso es arte puro.",
    ],
    closings=[
        "¿Te lo llevas? no cap.",
        "Dime talla y te lo aparto fr.",
        "Es un must, ¿te animas?",
        "Confía, te queda brutal.",
        "¿Lo quieres ya?",
    ],
    adjectives=[
        "iconic", "slay", "aesthetic", "fire",
        "underrated", "top tier", "vibe", "clean",
    ],
    connectors=["y", "además", "literal", "o sea", "tipo"],
    style_adjectives={
        "pantalon": "oversize vibe",
        "camiseta": "aesthetic",
        "jean": "baggy fit",
        "zapatillas": "fire",
        "accesorio": "statement piece",
    },
    writing_style="genz_informal",
)

ALL_PROFILES: list[ToneProfile] = [
    STREETWEAR, LUXURY, PREMIUM, CASUAL, MODERN_FASHION, GENZ_FASHION,
]

PROFILE_MAP: dict[str, ToneProfile] = {
    p.name: p for p in ALL_PROFILES
}

STYLE_TO_PROFILE: dict[str, str] = {
    "urbano": "streetwear",
    "casual": "casual",
    "deportivo": "casual",
    "elegante": "luxury",
    "formal": "luxury",
    "moderno": "modern_fashion",
    "trendy": "genz_fashion",
    "premium": "premium",
    "clasico": "premium",
    "genz": "genz_fashion",
    "street": "streetwear",
    "streetwear": "streetwear",
    "luxury": "luxury",
    "lujo": "luxury",
    "casual_chic": "premium",
    "fashion": "modern_fashion",
}


def get_profile(name: str) -> ToneProfile:
    return PROFILE_MAP.get(name, PREMIUM)


def detect_profile_from_style(style: str | None) -> ToneProfile:
    if style and style.lower() in STYLE_TO_PROFILE:
        return PROFILE_MAP[STYLE_TO_PROFILE[style.lower()]]
    return PREMIUM


def pick_random(items: list[str]) -> str:
    return random.choice(items)
