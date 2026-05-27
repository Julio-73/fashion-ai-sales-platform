import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.providers.openai_provider import OpenAIProvider
from app.smart_sales.entity_extractor import EntityExtractor, ExtractedEntities
from app.smart_sales.product_context import ProductContextEngine
from app.smart_sales.product_matcher import MatchedProduct, ProductMatcher
from app.smart_sales.recommendation_engine import RecommendationEngine
from app.smart_sales.sales_responder import SalesResponder

logger = logging.getLogger("ai_sales_agent.smart_sales.brain")


class SmartSalesBrain:
    def __init__(
        self,
        session: AsyncSession,
        provider: OpenAIProvider | None = None,
    ) -> None:
        self._session = session
        self._provider = provider or OpenAIProvider()
        self._entity_extractor = EntityExtractor()
        self._product_matcher = ProductMatcher()
        self._product_context = ProductContextEngine(session)
        self._recommendation_engine = RecommendationEngine(self._product_context)
        self._sales_responder = SalesResponder(self._recommendation_engine)

    async def generate_reply(
        self,
        *,
        empresa_id: UUID,
        user_message: str,
    ) -> str:
        entities = self._entity_extractor.extract(user_message)
        logger.info(
            "Entities extracted: product_type=%s size=%s color=%s gender=%s style=%s occasion=%s",
            entities.product_type, entities.size, entities.color,
            entities.gender, entities.style, entities.occasion,
        )

        if entities.has_product_intent or entities.raw_product_query:
            matched = await self._product_context.find_products(
                empresa_id=empresa_id,
                entities=entities,
                limit=10,
            )
            logger.info("Products matched: %d (best: %s)", len(matched),
                        matched[0].name if matched else "none")
            if self._provider.is_configured:
                return await self._generate_llm_reply(
                    empresa_id=empresa_id,
                    user_message=user_message,
                    entities=entities,
                    matched_products=matched,
                )
            return await self._sales_responder.generate_response(
                empresa_id=empresa_id,
                user_message=user_message,
                entities=entities,
                matched_products=matched,
            )

        if self._provider.is_configured:
            return await self._generate_llm_reply(
                empresa_id=empresa_id,
                user_message=user_message,
                entities=entities,
                matched_products=[],
            )

        return await self._sales_responder.generate_response(
            empresa_id=empresa_id,
            user_message=user_message,
            entities=entities,
            matched_products=[],
        )

    async def _generate_llm_reply(
        self,
        *,
        empresa_id: UUID,
        user_message: str,
        entities: ExtractedEntities,
        matched_products: list[MatchedProduct],
    ) -> str:
        try:
            context_parts = []
            if entities.has_any:
                context_parts.append("Intención del cliente:")
                if entities.product_type:
                    context_parts.append(f"- Producto: {entities.product_type}")
                if entities.size:
                    context_parts.append(f"- Talla: {entities.size}")
                if entities.color:
                    context_parts.append(f"- Color: {entities.color}")
                if entities.gender:
                    context_parts.append(f"- Género: {entities.gender}")
                if entities.style:
                    context_parts.append(f"- Estilo: {entities.style}")
                if entities.occasion:
                    context_parts.append(f"- Ocasión: {entities.occasion}")

            if matched_products:
                context_parts.append("\nProductos disponibles en catálogo:")
                for p in matched_products[:5]:
                    sizes = ", ".join(p.available_sizes) if p.available_sizes else "N/A"
                    colors = ", ".join(p.available_colors) if p.available_colors else "N/A"
                    stock_info = f"stock: {p.total_available_stock}" if p.total_available_stock > 0 else "sin stock"
                    context_parts.append(
                        f"- {p.name} | categoría: {p.category or 'N/A'} | "
                        f"precios: {p.price_range} | tallas: {sizes} | colores: {colors} | {stock_info}"
                    )

            product_context_str = "\n".join(context_parts)

            prompt = (
                "Eres un asistente de ventas experto para una tienda de moda online premium de Latinoamérica. "
                "Debes responder como un vendedor humano profesional, elegante, amable y moderno. "
                "Usa la información del catálogo proporcionada para dar respuestas precisas y convincentes. "
                "Sugiere productos relacionados y haz upsell de forma natural.\n\n"
                "REGLAS:\n"
                "- Responde en español LATAM natural\n"
                "- Si hay productos en stock, menciónalos con nombre, precio y variedad\n"
                "- Si NO hay productos exactos, sugiere alternativas cercanas\n"
                "- Si no hay nada relevante, sé amable y pregunta qué busca\n"
                "- NO inventes productos que no estén en el catálogo\n"
                "- Sé breve pero informativo (máximo 3-4 oraciones)\n"
                "- Usa un tono cálido pero profesional\n\n"
                f"{product_context_str}\n\n"
                f"Mensaje del cliente: {user_message}\n\n"
                "Responde como un asesor de moda:"
            )

            return await self._provider.generate(
                system_prompt=prompt,
                user_message=user_message,
                temperature=0.7,
                max_tokens=250,
            )
        except Exception:
            logger.exception("LLM reply generation failed, falling back to template")
            return await self._sales_responder.generate_response(
                empresa_id=empresa_id,
                user_message=user_message,
                entities=entities,
                matched_products=matched_products,
            )
