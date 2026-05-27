import logging
from uuid import UUID

from app.smart_sales.entity_extractor import ExtractedEntities
from app.smart_sales.humanization.follow_up_engine import FollowUpEngine
from app.smart_sales.humanization.response_humanizer import ResponseHumanizer
from app.smart_sales.humanization.style_system import StyleSystem
from app.smart_sales.memory.conversation_memory import ConversationContext
from app.smart_sales.product_matcher import MatchedProduct
from app.smart_sales.reasoning.advanced_recommender import AdvancedRecommender
from app.smart_sales.reasoning.confidence_scorer import ConfidenceResult, ConfidenceScorer
from app.smart_sales.recommendation_engine import RecommendationEngine

logger = logging.getLogger("ai_sales_agent.smart_sales.sales_responder")


STYLE_NAMES = {
    "oversize": "oversize",
    "slim_fit": "slim fit",
    "casual": "casual",
    "elegante": "elegante",
    "deportivo": "deportivo",
    "moderno": "moderno",
}


class SalesResponder:
    def __init__(
        self,
        recommendation_engine: RecommendationEngine,
        advanced_recommender: AdvancedRecommender | None = None,
        humanizer: ResponseHumanizer | None = None,
        style_system: StyleSystem | None = None,
        follow_up_engine: FollowUpEngine | None = None,
        confidence_scorer: ConfidenceScorer | None = None,
    ) -> None:
        self._recommendation_engine = recommendation_engine
        self._advanced_recommender = advanced_recommender or AdvancedRecommender(
            product_context=None  # type: ignore
        )
        self._humanizer = humanizer or ResponseHumanizer()
        self._style_system = style_system or StyleSystem()
        self._follow_up_engine = follow_up_engine or FollowUpEngine()
        self._confidence_scorer = confidence_scorer or ConfidenceScorer()

    async def generate_response(
        self,
        *,
        empresa_id: UUID,
        user_message: str,
        entities: ExtractedEntities,
        matched_products: list[MatchedProduct],
        memory_ctx: ConversationContext | None = None,
    ) -> str:
        entities_dict = {
            "product_type": entities.product_type,
            "size": entities.size,
            "color": entities.color,
            "gender": entities.gender,
            "style": entities.style,
            "occasion": entities.occasion,
        }

        in_stock = [p for p in matched_products if p.has_stock]
        no_stock = [p for p in matched_products if not p.has_stock and p.available_variants]

        confidence = self._confidence_scorer.evaluate(
            entities=entities_dict,
            matched_products=matched_products,
            has_history=bool(memory_ctx and memory_ctx.has_product_history()),
        )

        if in_stock:
            return await self._build_premium_stock_response(
                empresa_id=empresa_id,
                entities=entities_dict,
                products=in_stock[:5],
                confidence=confidence,
                memory_ctx=memory_ctx,
            )

        if no_stock:
            return self._build_premium_no_stock_response(entities_dict, no_stock[:3], confidence)

        similar = [p for p in matched_products if not p.available_variants]
        if similar:
            return self._build_premium_similar_response(entities_dict, similar[:3], confidence)

        return await self._build_premium_fallback_response(
            empresa_id=empresa_id, entities=entities_dict, user_message=user_message,
            confidence=confidence, memory_ctx=memory_ctx,
        )

    async def _build_premium_stock_response(
        self,
        *,
        empresa_id: UUID,
        entities: dict,
        products: list[MatchedProduct],
        confidence: ConfidenceResult,
        memory_ctx: ConversationContext | None = None,
    ) -> str:
        style_profile = self._style_system.detect_style_profile(entities, products)
        emoji = self._style_system.get_emoji(style_profile)

        parts = []
        opening = self._humanizer.pick_opening()
        parts.append(opening)

        product_type = entities.get("product_type", "opciones")
        if confidence.score >= 60:
            parts.append(f"Tenemos estas {product_type} disponibles{emoji}")
        else:
            parts.append(f"Mira estas {product_type} que pueden interesarte{emoji}")

        lines = []
        for p in products[:3]:
            price_str = p.price_range
            colors_str = ", ".join(p.available_colors[:3]) if p.available_colors else ""
            line_parts = []
            if entities.get("style") and entities["style"] != "casual":
                style_name = STYLE_NAMES.get(entities["style"], entities["style"])
                if style_name in p.name.lower() or style_name in (p.category or "").lower():
                    line_parts.append(f"{style_name.title()}")

            line_parts.append(p.name)
            name_str = " ".join(line_parts)
            color_info = f" — {colors_str}" if colors_str else ""
            price_info = f" ({price_str})" if price_str else ""
            lines.append(f"• {name_str}{color_info}{price_info}")

        parts.append("\n".join(lines))
        sizes_str = self._format_sizes(products, entities)
        if sizes_str:
            parts.append(sizes_str)
        parts.append("")

        upselling = await self._get_upselling(empresa_id, entities)
        if upselling:
            parts.append(upselling)
            parts.append("")

        closing = self._humanizer.pick_closing()
        parts.append(closing)
        if confidence.should_ask_before_recommend() and memory_ctx and memory_ctx.follow_up_count < 2:
            follow_ups = self._follow_up_engine.generate_questions(entities, confidence)
            if follow_ups:
                parts.append("\n" + follow_ups[0])

        result = "\n".join(parts)
        return self._humanizer.humanize_text(result)

    def _format_sizes(self, products: list[MatchedProduct], entities: dict) -> str:
        all_sizes = set()
        for p in products:
            all_sizes.update(p.available_sizes)
        if all_sizes:
            sorted_s = sorted(all_sizes, key=self._size_order)
            return f"Tallas disponibles: {', '.join(sorted_s)}."
        return ""

    def _build_premium_no_stock_response(
        self, entities: dict, products: list[MatchedProduct],
        confidence: ConfidenceResult,
    ) -> str:
        names = [p.name for p in products]
        parts = [
            "Tengo estos modelos, aunque algunos están sin stock en este momento 😅",
            ", ".join(names) + ".",
            "¿Quieres que verifique disponibilidad o te interesa otro modelo similar?",
        ]
        return " ".join(parts)

    def _build_premium_similar_response(
        self, entities: dict, products: list[MatchedProduct],
        confidence: ConfidenceResult,
    ) -> str:
        parts = [self._humanizer.pick_fallback_intro()]
        names = [f"{p.name} ({p.price_range})" for p in products if p.price_range]
        parts.append(", ".join(names) + ".")
        parts.append(self._humanizer.pick_closing())
        return " ".join(parts)

    async def _build_premium_fallback_response(
        self,
        *,
        empresa_id: UUID,
        entities: dict,
        user_message: str,
        confidence: ConfidenceResult,
        memory_ctx: ConversationContext | None = None,
    ) -> str:
        product_type = entities.get("product_type")
        color = entities.get("color")
        occasion = entities.get("occasion")
        style = entities.get("style")

        if product_type:
            recommendations = await self._recommendation_engine.generate_recommendations(
                empresa_id=empresa_id,
                current_product_type=product_type,
            )
            if recommendations:
                recs = ", ".join(r.category for r in recommendations[:3])
                return (f"No encontré exactamente {product_type} en este momento 😊 "
                        f"pero tenemos opciones similares en {recs}. "
                        f"{self._humanizer.pick_closing()}")
            return (f"Por ahora no tengo {product_type} disponible en el catálogo activo 🫤 "
                    f"¿Quieres explorar otras categorías? {self._humanizer.pick_follow_up()}")

        if style and not product_type:
            style_fallbacks = {
                "elegante": "¿Buscas vestidos, camisas formales o pantalones de vestir?",
                "deportivo": "¿Zapatillas, shorts o polos deportivos?",
                "casual": "¿Polos, jeans, chompas o zapatillas?",
                "oversize": "¿Chompas oversize, polos o pantalones jogger?",
            }
            msg = style_fallbacks.get(style, "¿Qué tipo de prenda buscas?")
            return f"¡Claro! Para estilo {style} tenemos varias opciones. {msg}"

        if color and not product_type:
            return (f"En color {color} tenemos varias opciones. "
                    f"¿Buscas polos, casacas, jeans o zapatillas en {color}?")

        if occasion:
            occasion_map = {
                "fiesta": "ropa elegante y de fiesta",
                "trabajo": "ropa formal y de oficina",
                "diario": "ropa casual y cómoda",
                "playa": "ropa de playa y verano",
                "deporte": "ropa deportiva",
            }
            desc = occasion_map.get(occasion, "prendas")
            return (f"Para {occasion} tenemos {desc}. "
                    f"Dime tipo de prenda, color o talla y te ayudo a encontrar lo ideal 😊")

        follow_up_count = memory_ctx.follow_up_count if memory_ctx else 0
        if follow_up_count == 0:
            greetings = [
                "¡Hola! 😊 ¿En qué puedo ayudarte hoy? Contamos con ropa moderna, desde polos y vestidos hasta casacas y accesorios. ¿Buscas algo en especial?",
                "¡Bienvenido! 🖐️ Soy tu asesor de moda. ¿Qué tipo de prenda buscas? Tenemos jeans, chompas, vestidos, zapatillas y mucho más.",
                "¡Hola! 👋 ¿Cómo puedo asistirte hoy? Si buscas ropa moderna y de calidad, estamos en el lugar correcto. ¿Qué necesitas?",
            ]
            return self._humanizer._pick_varied(greetings, set())
        if follow_up_count == 1:
            return "¿Tal vez una chompa, polo, casaca o jean? Cuéntame qué buscas y te ayudo a encontrar lo ideal 😊"
        return (
            "Dime qué tipo de prenda te interesa (polo, vestido, chompa, jean, etc.), "
            "color o talla y te muestro lo que tenemos disponible 🎯"
        )

    async def _get_upselling(self, empresa_id: UUID, entities: dict) -> str | None:
        product_type = entities.get("product_type")
        if not product_type:
            return None
        if self._advanced_recommender:
            return await self._advanced_recommender.get_premium_upsell_text(
                empresa_id=empresa_id,
                product_type=product_type,
            )
        return None

    def _size_order(self, size: str) -> int:
        order = {"XS": 0, "S": 1, "M": 2, "L": 3, "XL": 4, "XXL": 5}
        return order.get(size.upper(), 99)
