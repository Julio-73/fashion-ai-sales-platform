import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.providers.openai_provider import OpenAIProvider
from app.smart_sales.entity_extractor import EntityExtractor
from app.smart_sales.humanization.follow_up_engine import FollowUpEngine
from app.smart_sales.humanization.response_humanizer import ResponseHumanizer
from app.smart_sales.humanization.style_system import StyleSystem
from app.smart_sales.memory.conversation_memory import ConversationMemoryManager
from app.smart_sales.product_context import ProductContextEngine
from app.smart_sales.product_matcher import ProductMatcher
from app.smart_sales.ranking.product_ranker import ProductRankingEngine
from app.smart_sales.reasoning.advanced_recommender import AdvancedRecommender
from app.smart_sales.reasoning.confidence_scorer import ConfidenceScorer
from app.smart_sales.reasoning.contextual_reasoner import ContextualReasoner
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
        self._memory_manager = ConversationMemoryManager()
        self._entity_extractor = EntityExtractor()
        self._product_matcher = ProductMatcher()
        self._contextual_reasoner = ContextualReasoner()
        self._product_context = ProductContextEngine(session)
        self._product_ranker = ProductRankingEngine()
        self._advanced_recommender = AdvancedRecommender(self._product_context)
        self._recommendation_engine = RecommendationEngine(self._product_context)
        self._confidence_scorer = ConfidenceScorer()
        self._humanizer = ResponseHumanizer()
        self._style_system = StyleSystem()
        self._follow_up_engine = FollowUpEngine()
        self._sales_responder = SalesResponder(
            recommendation_engine=self._recommendation_engine,
            advanced_recommender=self._advanced_recommender,
            humanizer=self._humanizer,
            style_system=self._style_system,
            follow_up_engine=self._follow_up_engine,
            confidence_scorer=self._confidence_scorer,
        )

    async def generate_reply(
        self,
        *,
        empresa_id: UUID,
        user_message: str,
        conversation_id: UUID | None = None,
    ) -> str:
        memory_ctx = None
        if conversation_id:
            memory_ctx = self._memory_manager.get_or_create(conversation_id)
            memory_ctx.update_from_message(user_message)

        entities = self._entity_extractor.extract(user_message)
        entities_dict = {
            "product_type": entities.product_type,
            "size": entities.size,
            "color": entities.color,
            "gender": entities.gender,
            "style": entities.style,
            "occasion": entities.occasion,
        }

        if memory_ctx:
            memory_ctx.persist_entities(entities_dict)
            entities_dict = memory_ctx.merge_entities(entities_dict)
            entities_dict = self._contextual_reasoner.infer_context(user_message, entities_dict)

        if conversation_id:
            logger.info(
                "Memory context for conv %s: %s",
                conversation_id,
                memory_ctx.get_context_summary() if memory_ctx else "none",
            )

        logger.info(
            "Entities (after memory merge): product_type=%s size=%s color=%s gender=%s style=%s occasion=%s",
            entities_dict.get("product_type"), entities_dict.get("size"),
            entities_dict.get("color"), entities_dict.get("gender"),
            entities_dict.get("style"), entities_dict.get("occasion"),
        )

        matched = await self._product_context.find_products(
            empresa_id=empresa_id,
            entities=entities,
            limit=15,
        )

        if matched:
            matched = self._product_ranker.rank_products(
                matched,
                entities_dict,
                memory_context=memory_ctx.get_context_summary() if memory_ctx else None,
            )
            logger.info(
                "Ranked products: %d (best: %s score=%.1f)",
                len(matched), matched[0].name if matched else "none",
                matched[0].score if matched else 0,
            )

        confidence = self._confidence_scorer.evaluate(
            entities=entities_dict,
            matched_products=matched,
            has_history=bool(memory_ctx and memory_ctx.has_product_history()),
        )

        if confidence.should_recommend_directly() and self._provider.is_configured and matched:
            return await self._generate_llm_reply(
                empresa_id=empresa_id,
                user_message=user_message,
                entities_dict=entities_dict,
                matched_products=matched,
                memory_ctx=memory_ctx,
            )

        response = await self._sales_responder.generate_response(
            empresa_id=empresa_id,
            user_message=user_message,
            entities=entities,
            matched_products=matched,
            memory_ctx=memory_ctx,
        )

        if memory_ctx and confidence.should_ask_before_recommend():
            memory_ctx.follow_up_count += 1

        return response

    async def _generate_llm_reply(
        self,
        *,
        empresa_id: UUID,
        user_message: str,
        entities_dict: dict,
        matched_products: list,
        memory_ctx=None,
    ) -> str:
        try:
            context_parts = []
            if memory_ctx and memory_ctx.get_context_summary() != "sin contexto":
                context_parts.append(f"Historial reciente: {memory_ctx.get_context_summary()}")

            context_parts.append("Intención del cliente:")
            for key, label in [("product_type", "Producto"), ("size", "Talla"),
                               ("color", "Color"), ("gender", "Género"),
                               ("style", "Estilo"), ("occasion", "Ocasión")]:
                if entities_dict.get(key):
                    context_parts.append(f"- {label}: {entities_dict[key]}")

            if matched_products:
                context_parts.append("\nCatálogo priorizado (mejores matches primero):")
                for p in matched_products[:5]:
                    sizes = ", ".join(p.available_sizes) if p.available_sizes else "N/A"
                    colors = ", ".join(p.available_colors) if p.available_colors else "N/A"
                    stock_info = f"stock: {p.total_available_stock}" if p.total_available_stock > 0 else "sin stock"
                    context_parts.append(
                        f"- {p.name} | cat: {p.category or 'N/A'} | "
                        f"{p.price_range} | tallas: {sizes} | colores: {colors} | {stock_info} | score: {p.score}"
                    )

            product_context_str = "\n".join(context_parts)

            prompt = (
                "Eres un asesor de moda premium para una tienda online de Latinoamérica. "
                "Respondes como un vendedor humano real: cálido, elegante, conocedor de moda y con estilo.\n\n"
                "DIRECTRICES:\n"
                "- Habla en español LATAM natural, como un vendedor experto\n"
                "- Menciona productos con nombre, precio y disponibilidad real\n"
                "- Sugiere combinaciones y haz upsell natural\n"
                "- Sé breve pero informativo (máximo 4 oraciones)\n"
                "- NO inventes productos que no estén en el catálogo\n"
                "- Si no hay match exacto, sugiere la alternativa más cercana\n"
                "- Varía tu estilo de respuesta (no repitas frases)\n"
                "- Sé elegante, cálido y profesional\n\n"
                f"{product_context_str}\n\n"
                f"Cliente: {user_message}\n\n"
                "Responde como un asesor de moda:"
            )

            return await self._provider.generate(
                system_prompt=prompt,
                user_message=user_message,
                temperature=0.8,
                max_tokens=300,
            )
        except Exception:
            logger.exception("LLM reply failed, falling back to template")
            return await self._sales_responder.generate_response(
                empresa_id=empresa_id,
                user_message=user_message,
                entities=EntityExtractor().extract(user_message),
                matched_products=matched_products,
                memory_ctx=memory_ctx,
            )
