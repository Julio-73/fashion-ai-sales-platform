import logging
import random
import re

logger = logging.getLogger("ai_sales_agent.smart_sales.humanization.humanizer")


SYNONYM_MAP: dict[str, list[str]] = {
    "tener": ["contamos con", "disponemos de", "tenemos disponibles", "manejamos", "ofrecemos"],
    "disponible": ["disponible", "en stock", "listo para entrega", "con existencia", "en inventario"],
    "buscar": ["buscas", "necesitas", "quieres", "te interesa", "prefieres"],
    "ayudar": ["ayudarte", "asistirte", "apoyarte", "atenderte"],
    "modelo": ["modelo", "diseño", "estilo", "prenda", "producto"],
    "color": ["color", "tono", "variante", "acabado"],
    "precio": ["precio", "valor", "inversión", "costo"],
    "bueno": ["bueno", "excelente", "genial", "perfecto", "ideal"],
    "ver": ["ver", "revisar", "conocer", "explorar", "echar un vistazo a"],
    "querer": ["quieres", "gustaría", "te interesa", "prefieres", "te llama la atención"],
}

ROTATING_TEMPLATES_STOCK = [
    "{open} Tenemos {count} opción{plural} que te pueden interesar{emoji}.",
    "{open} Aquí van {count} {name_plural} disponibles{emoji}",
    "{open} Esta{plural} {name_plural} están disponibles ahora mismo.",
    "{open} Déjame mostrarte {count} {name_plural} que tenemos{emoji}",
    "Mira, justo tenemos {count} opción{plural} que te van a encantar{emoji}",
]

ROTATING_TEMPLATES_DETAIL = [
    "• {name} — {color_info}{price_info}",
    "• {name}{price_info}{color_info}",
    "• {name} ({color_info}){price_info}",
    "▸ {name}{price_info} — {color_info}",
    "→ {name}{color_info}{price_info}",
]

ROTATING_CLOSINGS = [
    "¿Te gusta alguna en particular?",
    "¿Cuál te llama más la atención?",
    "Dime si quieres más detalles de algún modelo.",
    "¿Quieres que te ayude a elegir?",
    "¿Te interesa alguno?",
    "Cuéntame si te gusta alguna opción.",
    "¿Vemos más opciones o alguna te convenció?",
]

ROTATING_FALLBACKS = [
    "No encontré exactamente ese producto, pero tenemos opciones similares que podrían gustarte 😊",
    "Justo ese modelo no está disponible ahora, pero mira estas alternativas:",
    "No tengo ese producto en este momento, sin embargo tenemos otras opciones muy interesantes:",
    "Ese producto no está en nuestro catálogo activo, pero estas alternativas te pueden servir:",
]

ROTATING_NO_RESULTS = [
    "Por ahora no tenemos productos que coincidan exactamente con tu búsqueda 🫤",
    "No encontré resultados para esa búsqueda específica.",
    "No tenemos nada exactamente así en este momento.",
]

ROTATING_FOLLOW_UP = [
    "¿Quieres que te muestre otras categorías?",
    "¿Buscas algo diferente? Cuéntame y te ayudo.",
    "¿Te interesa explorar otras opciones?",
    "Puedo ayudarte a buscar por tipo de prenda, color o estilo.",
]


class ResponseHumanizer:
    def __init__(self) -> None:
        self._used_openings: set[int] = set()
        self._used_closings: set[int] = set()
        self._used_templates: set[int] = set()

    def pick_opening(self) -> str:
        pool = [
            "Claro que sí 😊",
            "¡Sí tenemos!",
            "Por supuesto ✨",
            "¡Claro! 😊",
            "Perfecto, aquí van las opciones.",
            "Genial, tengo justo lo que buscas.",
            "¡Excelente elección!",
            "Por supuesto que sí, mira:",
        ]
        return self._pick_varied(pool, self._used_openings)

    def pick_closing(self) -> str:
        return self._pick_varied(ROTATING_CLOSINGS, self._used_closings)

    def pick_fallback_intro(self) -> str:
        return random.choice(ROTATING_FALLBACKS)

    def pick_no_results(self) -> str:
        return random.choice(ROTATING_NO_RESULTS)

    def pick_follow_up(self) -> str:
        return random.choice(ROTATING_FOLLOW_UP)

    def format_product_line(self, name: str, price: str, colors: list[str]) -> str:
        template = random.choice(ROTATING_TEMPLATES_DETAIL)
        color_info = f"en {', '.join(colors[:3])}" if colors else ""
        price_info = f" — {price}" if price else ""
        return template.format(
            name=name,
            price_info=price_info,
            color_info=f" ({color_info})" if color_info else "",
        )

    def humanize_text(self, text: str) -> str:
        for word, synonyms in SYNONYM_MAP.items():
            pattern = r'\b' + re.escape(word) + r'\b'
            if re.search(pattern, text, re.IGNORECASE) and random.random() < 0.3:
                replacement = random.choice(synonyms)
                text = re.sub(pattern, replacement, text, count=1, flags=re.IGNORECASE)
        return text

    def add_variety(self, text: str) -> str:
        if random.random() < 0.15:
            interjections = ["¡", "!", "— ", "… "]
            for ij in interjections:
                if random.random() < 0.3:
                    idx = random.randint(0, len(text))
                    text = text[:idx] + ij + text[idx:]
        return text

    def format_product_listing(self, products: list, style_profile: str, entities: dict) -> str:
        from app.smart_sales.humanization.style_system import StyleSystem
        style = StyleSystem()
        emoji = style.get_emoji(style_profile)

        opening = self.pick_opening()
        product_type = entities.get("product_type", "productos")
        name_plural_map = {
            "chompa": "chompas", "casaca": "casacas", "polo": "polos",
            "vestido": "vestidos", "pantalon": "pantalones", "jean": "jeans",
            "zapatillas": "zapatillas", "zapato": "zapatos",
        }
        plural = name_plural_map.get(product_type, product_type + "s" if product_type else "opciones")
        count = len(products)

        template = random.choice(ROTATING_TEMPLATES_STOCK)

        intro = template.format(
            open=opening,
            count=count,
            plural="es" if count != 1 else "",
            name_plural=plural,
            emoji=emoji,
        )

        lines = []
        for p in products[:5]:
            line = self.format_product_line(
                name=p.name,
                price=p.price_range,
                colors=p.available_colors,
            )
            lines.append(line)

        closing = self.pick_closing()

        parts = [intro, "\n".join(lines)]
        if self._used_closings:
            parts.append(closing)
        else:
            parts.append(closing)

        return "\n".join(parts)

    def _pick_varied(self, pool: list[str], used_set: set) -> str:
        available = [i for i in range(len(pool)) if i not in used_set]
        if not available:
            used_set.clear()
            available = list(range(len(pool)))
        idx = random.choice(available)
        used_set.add(idx)
        return pool[idx]

    def reset(self) -> None:
        self._used_openings.clear()
        self._used_closings.clear()
        self._used_templates.clear()
