import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.providers.openai_provider import OpenAIProvider
from app.smart_sales.entity_extractor import EntityExtractor
from app.smart_sales.conversational_closer.conversational_closer_engine import (
    ConversationalCloserEngine, CloserInput,
)
from app.smart_sales.human_sales.human_sales_engine import (
    HumanSalesPsychologyEngine, HumanSalesInput,
)
from app.smart_sales.conversational_router.conversational_router_engine import (
    ConversationalRouterEngine,
)
from app.smart_sales.humanization.follow_up_engine import FollowUpEngine
from app.smart_sales.humanization.response_humanizer import ResponseHumanizer
from app.smart_sales.humanization.sales_humanization_v6 import SalesHumanizationV6
from app.smart_sales.humanization.style_system import StyleSystem
from app.smart_sales.memory.conversation_memory import ConversationMemoryManager
from app.smart_sales.order_flow_engine import OrderFlowEngine
from app.smart_sales.product_context import ProductContextEngine
from app.smart_sales.product_matcher import ProductMatcher
from app.smart_sales.ranking.product_ranker import ProductRankingEngine
from app.smart_sales.reasoning.advanced_recommender import AdvancedRecommender
from app.smart_sales.reasoning.confidence_scorer import ConfidenceScorer
from app.smart_sales.reasoning.contextual_reasoner import ContextualReasoner
from app.smart_sales.recommendation_engine import RecommendationEngine
from app.smart_sales.sales_responder import SalesResponder
from app.smart_sales.contextual_commitment import (
    CommitmentStage,
    CommitmentStateMachine,
    ContextLockEngine,
    EliteProductConfirmation,
    ResponseFocusGuard,
    RejectionRecoveryEngine,
    SelectedProductTracker,
)

logger = logging.getLogger("ai_sales_agent.smart_sales.brain")

_shared_tracker = SelectedProductTracker()
_shared_state_machine = CommitmentStateMachine()
_shared_memory_manager = ConversationMemoryManager()
_shared_order_flow_engine = OrderFlowEngine()


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
        self._contextual_reasoner = ContextualReasoner()
        self._product_context = ProductContextEngine(session)
        self._product_ranker = ProductRankingEngine()
        self._advanced_recommender = AdvancedRecommender(self._product_context)
        self._recommendation_engine = RecommendationEngine(self._product_context)
        self._confidence_scorer = ConfidenceScorer()
        self._humanizer = ResponseHumanizer()
        self._sales_humanization_v6 = SalesHumanizationV6()
        self._style_system = StyleSystem()
        self._follow_up_engine = FollowUpEngine()
        self._human_sales = HumanSalesPsychologyEngine()
        self._conversational_closer = ConversationalCloserEngine()
        self._conversational_router = ConversationalRouterEngine()
        self._sales_responder = SalesResponder(
            recommendation_engine=self._recommendation_engine,
            advanced_recommender=self._advanced_recommender,
            humanizer=self._humanizer,
            style_system=self._style_system,
            follow_up_engine=self._follow_up_engine,
            confidence_scorer=self._confidence_scorer,
        )

        self._memory_manager = _shared_memory_manager
        self._order_flow_engine = _shared_order_flow_engine
        self._commitment_tracker = _shared_tracker
        self._commitment_state_machine = _shared_state_machine
        self._context_lock = ContextLockEngine(
            tracker=self._commitment_tracker,
            state_machine=self._commitment_state_machine,
        )
        self._product_confirmation = EliteProductConfirmation()
        self._response_focus_guard = ResponseFocusGuard()
        self._rejection_recovery = RejectionRecoveryEngine()

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

        conv_id_str = str(conversation_id) if conversation_id else f"emp_{empresa_id}"

        lock_result = self._context_lock.evaluate(
            conversation_id=conv_id_str,
            user_message=user_message,
        )

        commitment_data = self._commitment_tracker.get_or_create(conv_id_str)

        entities = self._entity_extractor.extract(user_message)
        order_result = self._order_flow_engine.process(
            conversation_id=conv_id_str,
            user_message=user_message,
            commitment=commitment_data,
            entities=entities,
        )
        if order_result.handled:
            if order_result.response and self._sales_humanization_v6.quality_score(order_result.response, commitment_data) == 0:
                logger.warning("Order Flow V7 generated low-quality response for conv %s", conv_id_str)
            if "reservado" in order_result.response.lower() or "reserva confirmada" in order_result.response.lower():
                self._commitment_tracker.mark_reserved(conv_id_str)
            logger.info("Order Flow V7 handled message: state=%s", order_result.state.value)
            return order_result.response

        active_v6 = self._sales_humanization_v6.process(
            user_message=user_message,
            commitment=commitment_data,
            entities=entities,
            matched_products=[],
        )
        if active_v6.handled:
            if active_v6.should_mark_reserved:
                self._commitment_tracker.mark_reserved(conv_id_str)
            logger.info("Sales Humanization V6 handled active-context message: stage=%s", active_v6.stage)
            return active_v6.response

        router_result = self._conversational_router.process(
            message=user_message,
            conversation_id=str(conversation_id) if conversation_id else None,
            empresa_id=str(empresa_id),
        )
        if router_result.handled:
            logger.info("Conversational router handled message as %s (conf=%.2f)", router_result.intent.value, router_result.confidence)
            return router_result.response

        recovery = None
        if lock_result.recovery_data:
            recovery = self._rejection_recovery.process(
                commitment=commitment_data,
                user_message=user_message,
            )

        if lock_result.should_bypass_catalog():
            logger.info(
                "Context lock active for conv %s: product=%s color=%s size=%s stage=%s",
                conv_id_str, lock_result.locked_product,
                lock_result.locked_color, lock_result.locked_size,
                lock_result.commitment_stage.value,
            )
            confirmation = self._product_confirmation.generate(
                commitment=commitment_data,
                user_message=user_message,
            )
            if confirmation:
                focused = await self._apply_human_sales_layer(
                    empresa_id=empresa_id,
                    user_message=user_message,
                    response=confirmation.text,
                    entities_dict={
                        "product_type": commitment_data.selected_category or "",
                        "size": commitment_data.selected_size or "",
                        "color": commitment_data.selected_color or "",
                        "gender": "",
                        "style": "",
                        "occasion": "",
                    },
                    matched=[],
                    conversation_id=conv_id_str,
                    memory_ctx=memory_ctx,
                )
                guard = self._response_focus_guard.check(focused, commitment_data)
                if guard.is_blocked:
                    logger.warning("Focus guard blocked human sales output, using raw confirmation")
                    return confirmation.text
                return focused

        if recovery and recovery.recovery_prompt:
            logger.info(
                "Recovery prompt for conv %s: category=%s",
                conv_id_str, recovery.recovered_category,
            )

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

        if recovery and recovery.needs_recovery:
            entities_dict = self._rejection_recovery.build_recovery_context(recovery, entities_dict)
            logger.info(
                "Recovery context applied: category=%s",
                recovery.recovered_category,
            )

        if conversation_id:
            logger.info(
                "Memory context for conv %s: %s",
                conversation_id,
                memory_ctx.get_context_summary() if memory_ctx else "none",
            )

        if lock_result.should_bypass_catalog():
            self._context_lock.lock_product(
                conv_id_str,
                product_name=lock_result.locked_product or "",
                category=lock_result.locked_category,
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

        if commitment_data.commitment_level.value >= 2 and not commitment_data.selected_product and matched:
            top = matched[0]
            self._context_lock.lock_product(
                conv_id_str,
                product_name=top.name,
                product_id=str(top.id) if hasattr(top, "id") and top.id else None,
                category=top.category if hasattr(top, "category") else None,
            )
            lock_result.is_locked = True
            lock_result.locked_product = top.name
            lock_result.locked_category = top.category if hasattr(top, "category") else None
            logger.info(
                "Post-extraction lock for conv %s: product=%s (commitment_level=%s)",
                conv_id_str, top.name, commitment_data.commitment_level,
            )
            commitment_data = self._commitment_tracker.get_or_create(conv_id_str)

        matched_v6 = self._sales_humanization_v6.process(
            user_message=user_message,
            commitment=commitment_data,
            entities=entities,
            matched_products=matched,
        )
        if matched_v6.should_lock_product and matched_v6.product_name:
            self._context_lock.lock_product(
                conv_id_str,
                product_name=matched_v6.product_name,
                product_id=matched_v6.product_id,
                category=matched_v6.product_category,
            )
            self._order_flow_engine.set_product(
                conv_id_str,
                product_name=matched_v6.product_name,
                product_id=matched_v6.product_id,
                product_category=matched_v6.product_category,
            )
            commitment_data = self._commitment_tracker.get_or_create(conv_id_str)
            order_result = self._order_flow_engine.process(
                conversation_id=conv_id_str,
                user_message=user_message,
                commitment=commitment_data,
                entities=entities,
            )
            if order_result.handled:
                logger.info("Order Flow V7 handled after product lock: state=%s", order_result.state.value)
                return order_result.response
            matched_v6 = self._sales_humanization_v6.process(
                user_message=user_message,
                commitment=commitment_data,
                entities=entities,
                matched_products=matched,
            )
        if matched_v6.handled:
            if matched_v6.should_mark_reserved:
                self._commitment_tracker.mark_reserved(conv_id_str)
            logger.info("Sales Humanization V6 handled matched message: stage=%s", matched_v6.stage)
            return matched_v6.response

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
            response = await self._generate_llm_reply(
                empresa_id=empresa_id,
                user_message=user_message,
                entities_dict=entities_dict,
                matched_products=matched,
                memory_ctx=memory_ctx,
            )
        else:
            response = await self._sales_responder.generate_response(
                empresa_id=empresa_id,
                user_message=user_message,
                entities=entities,
                matched_products=matched,
                memory_ctx=memory_ctx,
            )

            if memory_ctx and confidence.should_ask_before_recommend():
                memory_ctx.follow_up_count += 1

        response = await self._apply_human_sales_layer(
            empresa_id=empresa_id,
            user_message=user_message,
            response=response,
            entities_dict=entities_dict,
            matched=matched,
            conversation_id=str(conversation_id) if conversation_id else "",
            memory_ctx=memory_ctx,
        )

        if lock_result.should_bypass_catalog():
            guard = self._response_focus_guard.check(response, commitment_data)
            if guard.is_blocked:
                logger.warning(
                    "Focus guard blocked final response for conv %s: %s",
                    conv_id_str, guard.block_reason,
                )
                confirmation = self._product_confirmation.generate(
                    commitment=commitment_data,
                    user_message=user_message,
                )
                if confirmation:
                    return confirmation.text

        return response

    async def _apply_human_sales_layer(
        self,
        *,
        empresa_id: UUID | None = None,
        user_message: str,
        response: str,
        entities_dict: dict,
        matched: list,
        conversation_id: str,
        memory_ctx=None,
    ) -> str:
        try:
            top_product = matched[0] if matched else None
            total_stock = top_product.total_available_stock if top_product and hasattr(top_product, "total_available_stock") else 0

            input_data = HumanSalesInput(
                user_message=user_message,
                empresa_id=str(empresa_id) if empresa_id else "",
                conversation_id=conversation_id,
                product_name=top_product.name if top_product else "",
                product_category=top_product.category if top_product else "",
                product_style=entities_dict.get("style", ""),
                product_color=entities_dict.get("color", ""),
                product_occasion=entities_dict.get("occasion", ""),
                product_gender=entities_dict.get("gender", ""),
                product_size=entities_dict.get("size", ""),
                total_stock=total_stock,
                response=response,
            )

            # V3 — Human Sales Psychology
            v3_output = await self._human_sales.process(input_data=input_data)

            # V4 — Conversational Closer
            closer_input = CloserInput(
                user_message=user_message,
                conversation_id=conversation_id,
                response=v3_output.enhanced_response,
                product_name=input_data.product_name,
                product_category=input_data.product_category,
                product_color=input_data.product_color,
                product_size=input_data.product_size,
                product_style=input_data.product_style,
                product_occasion=input_data.product_occasion,
                product_gender=input_data.product_gender,
                total_stock=input_data.total_stock,
                available_sizes=top_product.available_sizes if top_product and hasattr(top_product, "available_sizes") else [],
                available_colors=top_product.available_colors if top_product and hasattr(top_product, "available_colors") else [],
                emotional_state=v3_output.emotional.state.value if v3_output.emotional else "",
                sales_stage=v3_output.current_stage.value if v3_output.current_stage else "",
                has_product_history=bool(matched) or (memory_ctx is not None and memory_ctx.has_product_history()),
                confidence_level=v3_output.emotional.state.value if v3_output.emotional else "",
            )

            v4_output = await self._conversational_closer.process(input_data=closer_input)
            return v4_output.response
        except Exception:
            logger.warning("Human sales layer failed, returning original response", exc_info=True)
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
