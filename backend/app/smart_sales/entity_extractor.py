import logging
import re
from dataclasses import dataclass

logger = logging.getLogger("ai_sales_agent.smart_sales.entity_extractor")

PRODUCT_ALIASES: dict[str, list[str]] = {
    "chompa": ["chompa", "chompas", "buzo", "buzos", "hoodie", "hoodies", "sudader", "sudadera", "poler"],
    "casaca": ["casaca", "casacas", "chaqueta", "jacket", "campera", "saco"],
    "polo": ["polo", "polos", "polera", "camiseta", "t-shirt", "tshirt", "remera"],
    "vestido": ["vestido", "vestidos", "vestidito", "vestdo", "enterizo"],
    "pantalon": ["pantalon", "pantalones", "jean", "jeans", "pant", "pants", "jogger", "joger", "jog"],
    "short": ["short", "shorts", "bermuda", "bermudas"],
    "falda": ["falda", "faldas", "pollera"],
    "zapatillas": ["zapatillas", "zapatilla", "tenis", "sneakers", "deportivos"],
    "zapatos": ["zapatos", "zapato", "tacones", "tacon"],
    "bikini": ["bikini", "traje de baño", "trajebaño", "trajebano", "bañador"],
    "camisa": ["camisa", "camisas"],
    "corbata": ["corbata"],
    "medias": ["medias", "calcetines"],
    "gorro": ["gorro", "gorra", "gorras"],
    "accesorio": ["accesorio", "accesorios", "cinturon", "cartera", "bolso", "bolsos", "mochila"],
}

SIZE_ALIASES: dict[str, str] = {
    "xs": "XS", "extra small": "XS",
    "s": "S", "small": "S", "pequeño": "S", "pequeno": "S",
    "m": "M", "medium": "M", "mediano": "M",
    "l": "L", "large": "L", "grande": "L",
    "xl": "XL", "extra large": "XL", "extra grande": "XL",
    "xxl": "XXL", "2xl": "XXL", "extra extra large": "XXL",
}

COLOR_ALIASES: dict[str, str] = {
    "rojo": "Rojo", "colorado": "Rojo", "rojizo": "Rojo",
    "azul": "Azul", "celeste": "Azul", "marino": "Azul",
    "negro": "Negro", "negra": "Negro", "negros": "Negro",
    "blanco": "Blanco", "blanca": "Blanco", "blancos": "Blanco",
    "verde": "Verde", "oliva": "Verde", "menta": "Verde",
    "amarillo": "Amarillo", "amarrillo": "Amarillo",
    "naranja": "Naranja", "anaranjado": "Naranja",
    "rosa": "Rosa", "rosado": "Rosa", "rosita": "Rosa", "pink": "Rosa",
    "morado": "Morado", "purpura": "Morado", "violeta": "Morado", "lila": "Morado",
    "gris": "Gris", "plomo": "Gris", "grises": "Gris",
    "beige": "Beige", "beis": "Beige", "crema": "Beige",
    "marrón": "Marrón", "marron": "Marrón", "cafe": "Marrón", "café": "Marrón", "carmelita": "Marrón",
    "dorado": "Dorado", "gold": "Dorado",
    "plateado": "Plateado", "silver": "Plateado",
}

GENDER_ALIASES: dict[str, str] = {
    "hombre": "hombre", "varon": "hombre", "masculino": "hombre", "men": "hombre", "man": "hombre",
    "mujer": "mujer", "femenino": "mujer", "woman": "mujer", "women": "mujer", "dama": "mujer",
    "unisex": "unisex", "niño": "unisex", "niña": "unisex", "kids": "unisex",
}

STYLE_ALIASES: dict[str, list[str]] = {
    "oversize": ["oversize", "holgado", "suelto", "ancho", "grande"],
    "slim_fit": ["slim fit", "slimfit", "ajustado", "ceñido", "entallado", "pegado"],
    "casual": ["casual", "diario", "informal", "comodo", "cómodo"],
    "elegante": ["elegante", "formal", "vestir", "fino", "chic", "fiesta", "cocktail", "gala"],
    "deportivo": ["deportivo", "sport", "deportes", "gym", "gimnasio", "running"],
    "moderno": ["moderno", "trendy", "actual", "moda", "estil"],
}

OCCASION_ALIASES: dict[str, list[str]] = {
    "fiesta": ["fiesta", "evento", "celebracion", "bod", "boda", "gala", "cocktail", "noche", "discoteca"],
    "trabajo": ["trabajo", "oficina", "formal", "profesional", "labour", "laboral"],
    "diario": ["diario", "casual", "todos los dias", "día a día", "cotidiano"],
    "playa": ["playa", "verano", "vacaciones", "tropical", "piscina", "balneario"],
    "deporte": ["deporte", "gym", "gimnasio", "ejercicio", "entrenar", "running", "sport"],
    "invierno": ["invierno", "frio", "frío", "abrigo", "otoño"],
}


@dataclass
class ExtractedEntities:
    product_type: str | None = None
    size: str | None = None
    color: str | None = None
    gender: str | None = None
    style: str | None = None
    occasion: str | None = None
    raw_product_query: str | None = None

    @property
    def has_any(self) -> bool:
        return any([self.product_type, self.size, self.color, self.gender, self.style, self.occasion])

    @property
    def has_product_intent(self) -> bool:
        return self.product_type is not None


class EntityExtractor:
    def extract(self, text: str) -> ExtractedEntities:
        if not text or not text.strip():
            return ExtractedEntities()
        normalized = text.lower().strip()

        product_type = self._match_product_type(normalized)
        size = self._match_size(normalized)
        color = self._match_color(normalized)
        gender = self._match_gender(normalized)
        style = self._match_style(normalized)
        occasion = self._match_occasion(normalized)
        raw_query = self._extract_raw_query(normalized)

        return ExtractedEntities(
            product_type=product_type,
            size=size,
            color=color,
            gender=gender,
            style=style,
            occasion=occasion,
            raw_product_query=raw_query,
        )

    def _match_product_type(self, text: str) -> str | None:
        for canonical, aliases in PRODUCT_ALIASES.items():
            for alias in aliases:
                if ' ' in alias:
                    if alias in text:
                        return canonical
                else:
                    pattern = r'\b' + re.escape(alias) + r's?\b'
                    if re.search(pattern, text):
                        return canonical
        return None

    def _match_size(self, text: str) -> str | None:
        size_pattern = r'\b(talla|talle|size)\s*[-:]?\s*(\w+)\b'
        m = re.search(size_pattern, text)
        if m:
            raw = m.group(2).lower()
            if raw in SIZE_ALIASES:
                return SIZE_ALIASES[raw]
        for alias, canonical in SIZE_ALIASES.items():
            if len(alias) <= 3:
                pattern = r'\b' + re.escape(alias) + r'\b'
                if re.search(pattern, text):
                    return canonical
        return None

    def _match_color(self, text: str) -> str | None:
        for alias, canonical in COLOR_ALIASES.items():
            pattern = r'\b' + re.escape(alias) + r's?\b'
            if re.search(pattern, text):
                return canonical
        return None

    def _match_gender(self, text: str) -> str | None:
        for alias, canonical in GENDER_ALIASES.items():
            pattern = r'\b' + re.escape(alias) + r's?\b'
            if re.search(pattern, text):
                return canonical
        return None

    def _match_style(self, text: str) -> str | None:
        for canonical, aliases in STYLE_ALIASES.items():
            for alias in aliases:
                if ' ' in alias:
                    if alias in text:
                        return canonical
                else:
                    pattern = r'\b' + re.escape(alias) + r's?\b'
                    if re.search(pattern, text):
                        return canonical
        return None

    def _match_occasion(self, text: str) -> str | None:
        for canonical, aliases in OCCASION_ALIASES.items():
            for alias in aliases:
                if ' ' in alias:
                    if alias in text:
                        return canonical
                else:
                    pattern = r'\b' + re.escape(alias) + r's?\b'
                    if re.search(pattern, text):
                        return canonical
        return None

    def _extract_raw_query(self, text: str) -> str | None:
        stop_words = {"quiero", "hay", "necesito", "busco", "tienen", "me", "un", "una",
                      "unos", "unas", "el", "la", "los", "las", "de", "para", "por",
                      "que", "en", "con", "y", "o", "a", "e", "se", "del", "al",
                      "hola", "buenas", "gracias", "chao", "adios", "ok", "si", "no"}
        query_words = [w for w in text.split() if w not in stop_words and len(w) > 2]
        return " ".join(query_words) if query_words else None
