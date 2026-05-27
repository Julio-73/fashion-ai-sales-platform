import logging
import random

logger = logging.getLogger("ai_sales_agent.smart_sales.humanization.style")


STYLE_PROFILES: dict[str, dict] = {
    "luxury": {
        "openings": [
            "Con mucho gusto.",
            "Será un placer ayudarte.",
            "Por supuesto, permíteme mostrarte lo mejor de nuestra colección.",
            "Encantado de poder ayudarte con esta selección.",
        ],
        "closings": [
            "Quedo atento a cualquier otra consulta que tengas.",
            "Espero que esta selección sea de tu agrado.",
            "¿Te gustaría agendar una asesoría personalizada?",
            "Estoy aquí para brindarte la mejor experiencia de compra.",
        ],
        "adjectives": ["exclusivo", "premium", "selecto", "distinguido", "cuidadosamente seleccionado"],
        "connectors": ["Además", "Asimismo", "Cabe destacar que", "Vale la pena mencionar"],
        "emojis": ["✨", "🌟", "💎", "👔", "👗"],
    },
    "casual": {
        "openings": [
            "¡Claro!",
            "¡Sí, mira!",
            "Por supuesto 😊",
            "¡Aquí te va!",
            "Con gusto.",
        ],
        "closings": [
            "¿Qué te parece?",
            "¿Te gusta alguna?",
            "Dime cuál te llama más la atención.",
            "¿Vamos por esa?",
        ],
        "adjectives": ["chévere", "bacán", "cool", "buenazo", "súper"],
        "connectors": ["Además", "También", "Por otro lado", "Igual"],
        "emojis": ["😊", "👌", "🔥", "💪", "✨"],
    },
    "modern_ecommerce": {
        "openings": [
            "Perfecto.",
            "Genial, acá van las opciones.",
            "¡Excelente elección!",
            "Mira lo que tenemos para ti.",
        ],
        "closings": [
            "¿Te interesa alguno en particular?",
            "¿Quieres más detalles de algún modelo?",
            "¿Te ayudo a elegir?",
            "¿Alguna te gustó más?",
        ],
        "adjectives": ["ideal", "perfecto", "moderno", "versátil", "trendy"],
        "connectors": ["También", "Además de eso", "Por cierto", "Y hablando de"],
        "emojis": ["🔥", "⭐", "✅", "👀", "🛒"],
    },
    "streetwear": {
        "openings": [
            "Obvio que sí 🔥",
            "Claro bro, mira esto.",
            "Tenemos harto estilo urbano.",
            "¡Sí! Esto es lo tuyo.",
        ],
        "closings": [
            "¿Cuál te gusta más?",
            "¿Te tira alguna?",
            "Dale, dime cuál te late.",
            "¿Vamos con alguna de esas?",
        ],
        "adjectives": ["fresh", "duro", "pesado", "cool", "bacán"],
        "connectors": ["Además", "También", "Y aparte", "Y si te gusta eso"],
        "emojis": ["🔥", "💯", "👟", "🧢", "🆒"],
    },
    "premium_fashion_advisor": {
        "openings": [
            "Te recomiendo especialmente...",
            "Basado en lo que buscas, esto te va a encantar.",
            "He seleccionado las mejores opciones para ti.",
            "Justo lo que necesitas, déjame mostrarte.",
        ],
        "closings": [
            "¿Te gusta alguna de estas opciones?",
            "Cuéntame si alguna te llama la atención.",
            "Puedo darte más detalles del modelo que prefieras.",
            "¿Quieres que te ayude con la talla y el color?",
        ],
        "adjectives": ["recomendado", "ideal", "perfecto", "excelente", "seleccionado"],
        "connectors": ["Además", "También te sugiero", "Otra opción interesante es", "Por cierto"],
        "emojis": ["✨", "🎯", "💫", "👔", "👗"],
    },
}


class StyleSystem:
    def detect_style_profile(self, entities: dict, matched_products: list) -> str:
        style = entities.get("style")
        product_type = entities.get("product_type")
        occasion = entities.get("occasion")

        if style == "elegante" or occasion == "fiesta":
            return "luxury" if random.random() < 0.5 else "premium_fashion_advisor"
        if style == "streetwear" or style == "oversize":
            return "streetwear"
        if style == "deportivo":
            return "casual"
        if product_type in ("zapatillas", "polo", "short"):
            return "streetwear" if random.random() < 0.4 else "modern_ecommerce"
        if occasion in ("trabajo",):
            return "premium_fashion_advisor"
        if product_type in ("vestido", "zapatos", "accesorio"):
            return "premium_fashion_advisor"

        return "modern_ecommerce"

    def get_profile(self, profile_name: str) -> dict:
        return STYLE_PROFILES.get(profile_name, STYLE_PROFILES["modern_ecommerce"])

    def get_opening(self, profile_name: str) -> str:
        profile = self.get_profile(profile_name)
        return random.choice(profile["openings"])

    def get_closing(self, profile_name: str) -> str:
        profile = self.get_profile(profile_name)
        return random.choice(profile["closings"])

    def get_emoji(self, profile_name: str) -> str:
        profile = self.get_profile(profile_name)
        return random.choice(profile["emojis"])

    def apply_adjective(self, text: str, profile_name: str) -> str:
        profile = self.get_profile(profile_name)
        adj = random.choice(profile["adjectives"])
        return text.replace("{adj}", adj)
