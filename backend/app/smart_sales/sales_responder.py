import logging
from uuid import UUID

from app.smart_sales.entity_extractor import ExtractedEntities
from app.smart_sales.product_matcher import MatchedProduct
from app.smart_sales.recommendation_engine import RecommendationEngine

logger = logging.getLogger("ai_sales_agent.smart_sales.sales_responder")


GREETINGS = ["Hola", "¡Hola!", "Hola 🖐️", "¡Hey!"]
AFFIRMATIONS = ["Claro", "Sí", "Por supuesto", "¡Claro que sí!", "Con gusto"]

STYLE_NAMES = {
    "oversize": "oversize",
    "slim_fit": "slim fit",
    "casual": "casual",
    "elegante": "elegante",
    "deportivo": "deportivo",
    "moderno": "moderno",
}


class SalesResponder:
    def __init__(self, recommendation_engine: RecommendationEngine) -> None:
        self._recommendation_engine = recommendation_engine

    async def generate_response(
        self,
        *,
        empresa_id: UUID,
        user_message: str,
        entities: ExtractedEntities,
        matched_products: list[MatchedProduct],
    ) -> str:
        in_stock = [p for p in matched_products if p.has_stock]
        no_stock = [p for p in matched_products if not p.has_stock and p.available_variants]

        if in_stock:
            return await self._build_stock_response(
                empresa_id=empresa_id,
                entities=entities,
                products=in_stock[:3],
                total_count=len(in_stock),
            )

        if no_stock:
            return self._build_no_stock_response(entities, no_stock[:2])

        similar = [p for p in matched_products if not p.available_variants]
        if similar:
            return self._build_similar_response(entities, similar[:3])

        return await self._build_fallback_response(empresa_id, entities, user_message)

    async def _build_stock_response(
        self,
        *,
        empresa_id: UUID,
        entities: ExtractedEntities,
        products: list[MatchedProduct],
        total_count: int,
    ) -> str:
        main = products[0]
        parts = []

        intro = self._pick_random(["Claro que sí 😊", "¡Sí tenemos!", "Por supuesto ✨", "¡Claro! 😊"])
        category_desc = f"de {entities.product_type}" if entities.product_type else "disponibles"
        parts.append(f"{intro} Contamos con {category_desc}.")

        collection = self._describe_product(main, entities)
        if collection:
            parts.append(collection)

        if len(products) > 1:
            alt = products[1]
            alt_desc = self._describe_product(alt, entities)
            if alt_desc:
                parts.append(f"También tenemos {alt_desc.lower()}.")

        if entities.size:
            size_variants = [p for p in products if p.available_sizes]
            if size_variants:
                all_sizes = set()
                for p in size_variants:
                    all_sizes.update(p.available_sizes)
                if all_sizes:
                    sorted_sizes = sorted(all_sizes, key=self._size_order)
                    parts.append(f"Stock disponible en tallas: {', '.join(sorted_sizes)}.")

        if entities.color and not any(entities.color.lower() in p.name.lower() for p in products):
            color_options = set()
            for p in products:
                color_options.update(p.available_colors)
            if color_options:
                colors_str = ", ".join(list(color_options)[:4])
                parts.append(f"Colores disponibles: {colors_str}.")

        rec_text = await self._recommendation_engine.get_upsell_text(
            empresa_id=empresa_id,
            product_type=entities.product_type,
            product_category=main.category,
        )
        if rec_text:
            parts.append(rec_text)

        outros = ["¿Te gustaría algún modelo en específico?", "¿Buscas algo más?", "¿Qué te parece?",
                   "¿Te ayudo con algo más?", "Dime si quieres más detalles."]
        parts.append(self._pick_random(outros))

        return " ".join(parts)

    def _build_no_stock_response(self, entities: ExtractedEntities, products: list[MatchedProduct]) -> str:
        parts = [f"{self._pick_random(AFFIRMATIONS)}, tenemos modelos similares pero actualmente algunos están sin stock 😅."]
        names = [p.name for p in products]
        parts.append(f"Tenemos: {', '.join(names)}.")
        parts.append("¿Quieres que verifique disponibilidad en tienda o te interesa algún otro modelo?")
        return " ".join(parts)

    def _build_similar_response(self, entities: ExtractedEntities, products: list[MatchedProduct]) -> str:
        parts = [f"{self._pick_random(AFFIRMATIONS)}, no encontré exactamente ese modelo pero tenemos opciones similares:"]
        names = [f"{p.name} ({p.price_range})" for p in products if p.price_range]
        parts.append(", ".join(names) + ".")
        parts.append("¿Te gusta alguna de estas opciones?")
        return " ".join(parts)

    async def _build_fallback_response(self, empresa_id: UUID, entities: ExtractedEntities, user_message: str) -> str:
        recommendations = await self._recommendation_engine.generate_recommendations(
            empresa_id=empresa_id,
            current_product_type=entities.product_type,
        )

        if entities.product_type:
            if recommendations:
                recs = ", ".join(r.category for r in recommendations[:3])
                return (f"No encontré exactamente ese modelo 😊 pero sí tenemos opciones similares "
                        f"en {recs}. ¿Te gustaría explorar alguna de estas categorías?")
            return (f"Por el momento no tengo disponible {entities.product_type} en nuestro catálogo activo 😊 "
                    f"¿Quieres que te muestre otras categorías como polos, casacas o accesorios?")

        if entities.color:
            return (f"{self._pick_random(AFFIRMATIONS)}. En color {entities.color} tenemos varias opciones "
                    f"en nuestra colección actual. ¿Buscas alguna prenda en específico? "
                    f"Te puedo recomendar polos, vestidos, casacas y más.")

        if entities.occasion:
            occasion_names = {
                "fiesta": "ropa elegante y de fiesta",
                "trabajo": "ropa formal y de oficina",
                "diario": "ropa casual y cómoda",
                "playa": "ropa de playa y verano",
                "deporte": "ropa deportiva",
            }
            desc = occasion_names.get(entities.occasion, "prendas")
            return (f"¡Claro! Para {entities.occasion} tenemos una colección de {desc}. "
                    f"¿Buscas algo en particular? Dime tipo de prenda, color o talla y te ayudo a encontrar lo ideal.")

        fallback = "¡Hola! 😊 ¿En qué puedo ayudarte hoy? Tenemos una amplia colección de ropa moderna, desde polos y vestidos hasta casacas y accesorios. ¿Buscas algo en especial?"
        return fallback

    def _describe_product(self, product: MatchedProduct, entities: ExtractedEntities) -> str:
        parts = []
        if product.category:
            parts.append(product.category)
        if entities.style:
            style_name = STYLE_NAMES.get(entities.style, entities.style)
            parts.insert(0, style_name)

        name_part = f"El modelo **{product.name}**" if product.name else "Uno de nuestros modelos"

        price_info = f" desde {product.price_range}" if product.price_range else ""

        colors = product.available_colors
        color_info = ""
        if colors:
            color_list = ", ".join(colors[:4])
            color_info = f" disponible en {color_list}"

        return f"{name_part}{price_info}{color_info}."

    def _pick_random(self, options: list[str]) -> str:
        import random
        return random.choice(options)

    def _size_order(self, size: str) -> int:
        order = {"XS": 0, "S": 1, "M": 2, "L": 3, "XL": 4, "XXL": 5}
        return order.get(size.upper(), 99)
