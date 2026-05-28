import random
import logging

from app.smart_sales.human_sales.tone_profiles import (
    ToneProfile, detect_profile_from_style,
    pick_random,
)

logger = logging.getLogger("smart_sales.human_sales.personality")


STREETWEAR_STATEMENTS: list[str] = [
    "Ese modelo está brutal.",
    "Te quedaría demasiado bien con joggers negros.",
    "Esa pieza es un must.",
    "Está cañón el modelo.",
    "Con eso vas a volar.",
    "Te va a quedar fresh total.",
]

LUXURY_STATEMENTS: list[str] = [
    "Excelente elección. Ese modelo tiene un acabado premium muy elegante.",
    "Una pieza de alta distinción.",
    "La calidad de este modelo es excepcional.",
    "Un diseño que refleja buen gusto.",
    "Es de lo más sofisticado que tenemos.",
]

PREMIUM_STATEMENTS: list[str] = [
    "Buena elección, es de nuestros modelos premium.",
    "Me encanta tu estilo, ese modelo es increíble.",
    "Esa pieza destaca por su calidad y diseño.",
    "Es una prenda que marca la diferencia.",
    "Te va a encantar la calidad.",
]

CASUAL_STATEMENTS: list[str] = [
    "Esa es una buena opción para el día a día.",
    "Súper cómodo y con estilo.",
    "Ideal para un look casual pero con onda.",
    "Te va a servir para mil looks.",
    "Es bien versátil, te va a encantar.",
]

MODERN_STATEMENTS: list[str] = [
    "Ideal para un look contemporáneo.",
    "Perfecto para quienes buscan estilo actual.",
    "Un diseño pensado para la moda de hoy.",
    "Se adapta perfectamente a las tendencias actuales.",
    "Moderno, versátil y con mucho estilo.",
]

GENZ_STATEMENTS: list[str] = [
    "OMG ese modelo es un vibe total.",
    "Te va a quedar aesthetic.",
    "Eso es literalmente fire.",
    "Es un fit perfecto para cualquier look.",
    "Confía, es top tier.",
]

PROFILE_STATEMENTS: dict[str, list[str]] = {
    "streetwear": STREETWEAR_STATEMENTS,
    "luxury": LUXURY_STATEMENTS,
    "premium": PREMIUM_STATEMENTS,
    "casual": CASUAL_STATEMENTS,
    "modern_fashion": MODERN_STATEMENTS,
    "genz_fashion": GENZ_STATEMENTS,
}

_LAST_STATEMENT: dict[str, int] = {}


class PersonalityEngine:
    def detect_profile(
        self,
        style: str | None = None,
        category: str | None = None,
        gender: str | None = None,
    ) -> ToneProfile:
        return detect_profile_from_style(style)

    def get_profile_emoji(self, profile: ToneProfile) -> str:
        return random.choice(profile.emojis)

    def get_profile_statement(self, profile_name: str) -> str:
        pool = PROFILE_STATEMENTS.get(profile_name, PREMIUM_STATEMENTS)
        key = f"stmt_{profile_name}"
        last = _LAST_STATEMENT.get(key, -1)
        available = [i for i in range(len(pool)) if i != last]
        if not available:
            available = list(range(len(pool)))
        idx = random.choice(available)
        _LAST_STATEMENT[key] = idx
        return pool[idx]

    def get_opening(self, profile: ToneProfile) -> str:
        return pick_random(profile.openings)

    def get_closing(self, profile: ToneProfile) -> str:
        return pick_random(profile.closings)

    def get_connector(self, profile: ToneProfile) -> str:
        return pick_random(profile.connectors)

    def enhance_with_personality(self, response: str, profile_name: str) -> str:
        stmt = self.get_profile_statement(profile_name)
        return f"{stmt} {response}"

    def reset(self) -> None:
        _LAST_STATEMENT.clear()
