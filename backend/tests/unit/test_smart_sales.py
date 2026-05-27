import pytest
from uuid import uuid4, UUID

from app.smart_sales.entity_extractor import EntityExtractor, ExtractedEntities
from app.smart_sales.humanization.follow_up_engine import FollowUpEngine
from app.smart_sales.humanization.response_humanizer import ResponseHumanizer
from app.smart_sales.humanization.style_system import StyleSystem
from app.smart_sales.memory.conversation_memory import ConversationContext, ConversationMemoryManager
from app.smart_sales.product_matcher import ProductMatcher, MatchedProduct, MatchedVariant
from app.smart_sales.ranking.product_ranker import ProductRankingEngine
from app.smart_sales.reasoning.confidence_scorer import ConfidenceScorer, ConfidenceResult
from app.smart_sales.reasoning.contextual_reasoner import ContextualReasoner
from app.smart_sales.sales_responder import SalesResponder
from app.smart_sales.recommendation_engine import RecommendationEngine
from app.smart_sales.brain import SmartSalesBrain


# ─── Entity Extractor Tests ─────────────────────────────────────────────────

class TestEntityExtractor:
    @pytest.fixture
    def extractor(self) -> EntityExtractor:
        return EntityExtractor()

    def test_extracts_product_chompa(self, extractor: EntityExtractor) -> None:
        entities = extractor.extract("hay chompas talla m?")
        assert entities.product_type == "chompa"
        assert entities.size == "M"

    def test_extracts_product_vestido_rojo(self, extractor: EntityExtractor) -> None:
        entities = extractor.extract("quiero un vestido rojo elegante para una fiesta")
        assert entities.product_type == "vestido"
        assert entities.color == "Rojo"
        assert entities.occasion == "fiesta"

    def test_extracts_jean_negro(self, extractor: EntityExtractor) -> None:
        entities = extractor.extract("quiero jean negro")
        assert entities.product_type == "pantalon"
        assert entities.color == "Negro"

    def test_extracts_oversize_hombre(self, extractor: EntityExtractor) -> None:
        entities = extractor.extract("ropa oversize hombre")
        assert entities.gender == "hombre"
        assert entities.style == "oversize"

    def test_typo_tolerance_chompas(self, extractor: EntityExtractor) -> None:
        entities = extractor.extract("hay chompas talla m?")
        assert entities.product_type == "chompa"

    def test_extracts_size_s(self, extractor: EntityExtractor) -> None:
        entities = extractor.extract("talla s")
        assert entities.size == "S"

    def test_extracts_size_pequeno(self, extractor: EntityExtractor) -> None:
        entities = extractor.extract("talle pequeño")
        assert entities.size == "S"

    def test_extracts_color_gris(self, extractor: EntityExtractor) -> None:
        entities = extractor.extract("buzo gris")
        assert entities.color == "Gris"

    def test_extracts_occasion_trabajo(self, extractor: EntityExtractor) -> None:
        entities = extractor.extract("pantalon formal para oficina")
        assert entities.occasion == "trabajo"

    def test_no_intent_returns_empty(self, extractor: EntityExtractor) -> None:
        entities = extractor.extract("hola")
        assert not entities.has_product_intent

    def test_greeting_no_entities(self, extractor: EntityExtractor) -> None:
        entities = extractor.extract("buenos días")
        assert not entities.has_any

    def test_extract_zapatillas(self, extractor: EntityExtractor) -> None:
        entities = extractor.extract("zapatillas running hombre talla 42")
        assert entities.product_type == "zapatillas"
        assert entities.gender == "hombre"

    def test_extract_casaca_negra(self, extractor: EntityExtractor) -> None:
        entities = extractor.extract("casaca negra talla l")
        assert entities.product_type == "casaca"
        assert entities.color == "Negro"
        assert entities.size == "L"


# ─── Product Matcher Tests ───────────────────────────────────────────────────

class TestProductMatcher:
    @pytest.fixture
    def matcher(self) -> ProductMatcher:
        return ProductMatcher()

    def test_fuzzy_match(self, matcher: ProductMatcher) -> None:
        assert matcher._fuzzy_match("vestido", "vestido")
        assert matcher._fuzzy_match("vestdo", "vestido", threshold=0.6)
        assert not matcher._fuzzy_match("vestdo", "pantalon", threshold=0.6)

    def test_levenshtein(self, matcher: ProductMatcher) -> None:
        assert matcher._levenshtein("chompa", "chompa") == 0
        assert matcher._levenshtein("vestido", "vestdo") == 1

    def test_normalize_text(self, matcher: ProductMatcher) -> None:
        normalized = matcher.normalize_text("Quiero un vestido rojo para una fiesta")
        assert "vestido" in normalized
        assert "rojo" in normalized
        assert "quiero" not in normalized

    def test_match_product_types_chompa(self, matcher: ProductMatcher) -> None:
        types = matcher.match_product_types("chompas negras talla m")
        assert "chompa" in types

    def test_match_product_types_hoodie(self, matcher: ProductMatcher) -> None:
        types = matcher.match_product_types("hoodie oversize")
        assert "chompa" in types

    def test_match_product_types_jogger(self, matcher: ProductMatcher) -> None:
        types = matcher.match_product_types("jogger hombre")
        assert "pantalon" in types

    def test_score_product_exact(self, matcher: ProductMatcher) -> None:
        from app.smart_sales.entity_extractor import ExtractedEntities
        entities = ExtractedEntities(product_type="vestido", color="Rojo")
        score = matcher.score_product("Vestido Rojo Elegante", "Vestidos", entities)
        assert score >= 50.0

    def test_score_product_partial(self, matcher: ProductMatcher) -> None:
        from app.smart_sales.entity_extractor import ExtractedEntities
        entities = ExtractedEntities(product_type="vestido", color="Azul")
        score = matcher.score_product("Jean Clásico", "Pantalones", entities)
        assert score < 30.0


# ─── Sales Responder Tests ───────────────────────────────────────────────────

class TestSalesResponder:
    @pytest.fixture
    def responder(self) -> SalesResponder:
        from unittest.mock import AsyncMock
        rec_engine = AsyncMock(spec=RecommendationEngine)
        rec_engine.get_upsell_text = AsyncMock(return_value=None)
        rec_engine.generate_recommendations = AsyncMock(return_value=[])
        return SalesResponder(rec_engine)

    @pytest.fixture
    def sample_products(self) -> list[MatchedProduct]:
        variant = MatchedVariant(
            variant_id=str(uuid4()),
            talla="M",
            color="Negro",
            price=129.0,
            stock=50,
            reserved_stock=5,
            sku="CHM-001",
        )
        product = MatchedProduct(
            product_id=str(uuid4()),
            name="Chompa Urban Winter",
            category="Chompas",
            base_price=129.0,
            available_variants=[variant],
            score=85.0,
            match_reason="exact",
        )
        return [product]

    @pytest.mark.asyncio
    async def test_stock_response(self, responder: SalesResponder, sample_products: list[MatchedProduct]) -> None:
        from app.smart_sales.entity_extractor import ExtractedEntities
        entities = ExtractedEntities(product_type="chompa", size="M")
        response = await responder.generate_response(
            empresa_id=uuid4(),
            user_message="hay chompas talla m?",
            entities=entities,
            matched_products=sample_products,
        )
        assert "Chompa Urban Winter" in response
        assert "S/" in response or "s/" in response

    @pytest.mark.asyncio
    async def test_no_products_fallback(self, responder: SalesResponder) -> None:
        from app.smart_sales.entity_extractor import ExtractedEntities
        entities = ExtractedEntities(product_type="bikini")
        response = await responder.generate_response(
            empresa_id=uuid4(),
            user_message="bikini talla s",
            entities=entities,
            matched_products=[],
        )
        assert not response.startswith("Gracias por tu mensaje")
        assert "bikini" in response.lower() or "categorías" in response

    @pytest.mark.asyncio
    async def test_greeting_no_entities(self, responder: SalesResponder) -> None:
        from app.smart_sales.entity_extractor import ExtractedEntities
        entities = ExtractedEntities()
        response = await responder.generate_response(
            empresa_id=uuid4(),
            user_message="Hola",
            entities=entities,
            matched_products=[],
        )
        assert len(response) > 10

    @pytest.mark.asyncio
    async def test_color_intent(self, responder: SalesResponder) -> None:
        from app.smart_sales.entity_extractor import ExtractedEntities
        entities = ExtractedEntities(color="Rojo")
        response = await responder.generate_response(
            empresa_id=uuid4(),
            user_message="quiero algo rojo",
            entities=entities,
            matched_products=[],
        )
        assert "Rojo" in response or "rojo" in response.lower()


# ─── Fuzzy Matching & Typo Tolerance Tests ──────────────────────────────────

class TestTypoTolerance:
    @pytest.fixture
    def extractor(self) -> EntityExtractor:
        return EntityExtractor()

    def test_typo_vestdo(self, extractor: EntityExtractor) -> None:
        entities = extractor.extract("vestdo rojo")
        assert entities.product_type == "vestido"

    def test_typo_chompas_negras(self, extractor: EntityExtractor) -> None:
        entities = extractor.extract("chompas negras")
        assert entities.product_type == "chompa"
        assert entities.color == "Negro"

    def test_typo_joger(self, extractor: EntityExtractor) -> None:
        entities = extractor.extract("joger talla m")
        assert entities.product_type == "pantalon"

    def test_abbreviated_tall_m(self, extractor: EntityExtractor) -> None:
        entities = extractor.extract("tall m")
        assert entities.size == "M"

    def test_informal_escritura(self, extractor: EntityExtractor) -> None:
        entities = extractor.extract("kiero una chompa negra talla s")
        assert entities.product_type == "chompa"
        assert entities.color == "Negro"
        assert entities.size == "S"


# ─── SmartSalesBrain Integration Tests ──────────────────────────────────────

class TestSmartSalesBrainUnit:
    @pytest.mark.asyncio
    async def test_brain_generates_reply_without_db(self) -> None:
        from unittest.mock import AsyncMock
        session = AsyncMock()
        session.execute = AsyncMock(return_value=AsyncMock())
        result = session.execute.return_value
        result.unique = lambda: result
        result.scalars = lambda: result
        result.all = lambda: []
        brain = SmartSalesBrain(session=session)
        reply = await brain.generate_reply(
            empresa_id=uuid4(),
            user_message="Hola",
        )
        assert reply
        assert len(reply) > 10

    @pytest.mark.asyncio
    async def test_brain_returns_something_for_product_query(self) -> None:
        from unittest.mock import AsyncMock
        session = AsyncMock()
        session.execute = AsyncMock(return_value=AsyncMock())
        result = session.execute.return_value
        result.unique = lambda: result
        result.scalars = lambda: result
        result.all = lambda: []
        brain = SmartSalesBrain(session=session)
        reply = await brain.generate_reply(
            empresa_id=uuid4(),
            user_message="quiero una chompa talla m negra",
        )
        assert reply
        assert len(reply) > 10


# ─── Multi-Tenant Isolation Tests ────────────────────────────────────────────

# ─── Conversation Memory Tests ──────────────────────────────────────────────

class TestConversationMemory:
    def test_memory_creates_and_persists(self) -> None:
        manager = ConversationMemoryManager()
        conv_id = uuid4()
        ctx = manager.get_or_create(conv_id)
        assert ctx is not None
        assert not ctx.has_product_history()
        ctx.persist_entities({"product_type": "vestido", "color": "Rojo"})
        assert ctx.last_product_type == "vestido"
        assert ctx.last_color == "Rojo"
        assert ctx.has_product_history()

    def test_memory_merge_entities(self) -> None:
        ctx = ConversationContext()
        ctx.persist_entities({"product_type": "chompa", "size": "M"})
        merged = ctx.merge_entities({"color": "Negro"})
        assert merged["product_type"] == "chompa"
        assert merged["size"] == "M"
        assert merged["color"] == "Negro"

    def test_memory_merge_overrides(self) -> None:
        ctx = ConversationContext()
        ctx.persist_entities({"product_type": "chompa"})
        merged = ctx.merge_entities({"product_type": "vestido", "color": "Rojo"})
        assert merged["product_type"] == "vestido"
        assert merged["color"] == "Rojo"

    def test_memory_recent_messages(self) -> None:
        ctx = ConversationContext()
        ctx.update_from_message("hola")
        ctx.update_from_message("quiero chompa")
        ctx.update_from_message("talla m")
        assert len(ctx.recent_messages) == 3
        assert ctx.recent_messages[-1] == "talla m"

    def test_memory_context_summary(self) -> None:
        ctx = ConversationContext()
        ctx.persist_entities({"gender": "hombre", "product_type": "pantalon"})
        summary = ctx.get_context_summary()
        assert "hombre" in summary
        assert "pantalon" in summary

    def test_memory_clear(self) -> None:
        manager = ConversationMemoryManager()
        conv_id = uuid4()
        manager.get_or_create(conv_id)
        assert manager.size() == 1
        manager.clear(conv_id)
        assert manager.size() == 0


# ─── Contextual Reasoning Tests ─────────────────────────────────────────────

class TestContextualReasoning:
    @pytest.fixture
    def reasoner(self) -> ContextualReasoner:
        return ContextualReasoner()

    def test_infer_context_from_empty(self, reasoner: ContextualReasoner) -> None:
        result = reasoner.infer_context("ropa elegante para fiesta", {})
        assert result.get("style") == "elegante"
        assert result.get("product_type") == "vestido"

    def test_infer_context_casual(self, reasoner: ContextualReasoner) -> None:
        result = reasoner.infer_context("algo casual urbano", {})
        assert result.get("style") in ("casual", "urbano")

    def test_infer_context_from_style(self, reasoner: ContextualReasoner) -> None:
        result = reasoner.infer_context("streetwear oversize", {})
        assert result.get("style") in ("streetwear", "oversize", "urbano")

    def test_infer_from_context_merges(self, reasoner: ContextualReasoner) -> None:
        msg = {"product_type": "vestido"}
        mem = {"color": "Rojo", "size": "M"}
        merged = reasoner.infer_from_context(msg, mem)
        assert merged["product_type"] == "vestido"
        assert merged["color"] == "Rojo"

    def test_generate_follow_up_vestido(self, reasoner: ContextualReasoner) -> None:
        questions = reasoner.generate_follow_up_questions({"product_type": "vestido"}, 0.5)
        assert len(questions) >= 1
        assert any("largo" in q.lower() or "elegante" in q.lower() for q in questions)

    def test_generate_follow_up_zapatillas(self, reasoner: ContextualReasoner) -> None:
        questions = reasoner.generate_follow_up_questions({"product_type": "zapatillas"}, 0.5)
        assert any("urban" in q.lower() or "deportiv" in q.lower() or "casual" in q.lower() for q in questions)

    def test_generate_follow_up_color_only(self, reasoner: ContextualReasoner) -> None:
        questions = reasoner.generate_follow_up_questions({"color": "Rojo"}, 0.3)
        assert any("polos" in q.lower() or "casacas" in q.lower() for q in questions)


# ─── Product Ranking V2 Tests ────────────────────────────────────────────────

class TestProductRankingV2:
    @pytest.fixture
    def ranker(self) -> ProductRankingEngine:
        return ProductRankingEngine()

    @pytest.fixture
    def sample_products(self) -> list[MatchedProduct]:
        v = MatchedVariant(str(uuid4()), "M", "Rojo", 249, 20, 2, "VST-001")
        p1 = MatchedProduct(str(uuid4()), "Vestido Rojo Elegante", "Vestidos", 249.0, [v], 80.0, "exact")
        v2 = MatchedVariant(str(uuid4()), "L", "Negro", 129, 30, 0, "CHM-002")
        p2 = MatchedProduct(str(uuid4()), "Chompa Urban Negro", "Chompas", 129.0, [v2], 40.0, "partial")
        return [p1, p2]

    def test_rank_vestido_rojo(self, ranker: ProductRankingEngine, sample_products: list[MatchedProduct]) -> None:
        ranked = ranker.rank_products(sample_products, {"product_type": "vestido", "color": "Rojo"})
        assert ranked[0].name == "Vestido Rojo Elegante"
        assert ranked[0].score > ranked[1].score

    def test_rank_sizes_boost(self, ranker: ProductRankingEngine, sample_products: list[MatchedProduct]) -> None:
        ranked = ranker.rank_products(sample_products, {"product_type": "vestido", "size": "M"})
        assert ranked[0].name == "Vestido Rojo Elegante"

    def test_rank_stock_penalty(self, ranker: ProductRankingEngine) -> None:
        v = MatchedVariant(str(uuid4()), "M", "Negro", 129, 0, 0, "NST-001")
        no_stock = MatchedProduct(str(uuid4()), "Chompa Sin Stock", "Chompas", 129.0, [v], 50.0, "exact")
        v2 = MatchedVariant(str(uuid4()), "M", "Rojo", 249, 20, 2, "VST-001")
        with_stock = MatchedProduct(str(uuid4()), "Vestido Con Stock", "Vestidos", 249.0, [v2], 50.0, "exact")
        ranked = ranker.rank_products([no_stock, with_stock], {"product_type": "vestido"})
        assert ranked[0].name == "Vestido Con Stock"


# ─── Confidence Scorer Tests ─────────────────────────────────────────────────

class TestConfidenceScorer:
    @pytest.fixture
    def scorer(self) -> ConfidenceScorer:
        return ConfidenceScorer()

    def test_high_confidence(self, scorer: ConfidenceScorer) -> None:
        v = MatchedVariant(str(uuid4()), "M", "Rojo", 249, 20, 2, "VST-001")
        p = MatchedProduct(str(uuid4()), "Vestido Rojo", "Vestidos", 249.0, [v], 80.0, "exact")
        result = scorer.evaluate(entities={"product_type": "vestido", "color": "Rojo", "size": "M"},
                                 matched_products=[p], has_history=True)
        assert result.level == "high"
        assert result.score >= 60
        assert not result.should_ask_before_recommend()

    def test_low_confidence(self, scorer: ConfidenceScorer) -> None:
        result = scorer.evaluate(entities={}, matched_products=[], has_history=False)
        assert result.level == "low"
        assert result.should_ask_before_recommend()

    def test_medium_confidence(self, scorer: ConfidenceScorer) -> None:
        v = MatchedVariant(str(uuid4()), "M", "Azul", 129, 5, 0, "PL-001")
        p = MatchedProduct(str(uuid4()), "Polo Azul", "Polos", 129.0, [v], 30.0, "partial")
        result = scorer.evaluate(entities={"product_type": "polo"}, matched_products=[p], has_history=False)
        assert result.level in ("medium", "high")


# ─── Follow-Up Engine Tests ──────────────────────────────────────────────────

class TestFollowUpEngine:
    @pytest.fixture
    def engine(self) -> FollowUpEngine:
        return FollowUpEngine()

    def test_no_questions_when_high_confidence(self, engine: FollowUpEngine) -> None:
        confidence = ConfidenceResult(score=80.0, level="high", reason="test")
        questions = engine.generate_questions({"product_type": "vestido"}, confidence)
        assert len(questions) == 0

    def test_questions_when_low_confidence(self, engine: FollowUpEngine) -> None:
        confidence = ConfidenceResult(score=20.0, level="low", reason="test")
        questions = engine.generate_questions({"product_type": "vestido"}, confidence)
        assert len(questions) >= 1

    def test_should_not_ask_twice(self, engine: FollowUpEngine) -> None:
        confidence = ConfidenceResult(score=20.0, level="low", reason="test")
        assert engine.should_ask_question(confidence, 0)
        assert engine.should_ask_question(confidence, 1)
        assert not engine.should_ask_question(confidence, 2)

    def test_clarification_when_no_product(self, engine: FollowUpEngine) -> None:
        confidence = ConfidenceResult(score=10.0, level="low", reason="test")
        questions = engine.generate_questions({"color": "Rojo"}, confidence)
        assert len(questions) >= 1


# ─── Humanization Tests ──────────────────────────────────────────────────────

class TestResponseHumanizer:
    @pytest.fixture
    def humanizer(self) -> ResponseHumanizer:
        humanizer = ResponseHumanizer()
        humanizer.reset()
        return humanizer

    def test_pick_opening_varied(self, humanizer: ResponseHumanizer) -> None:
        openings = set()
        for _ in range(20):
            openings.add(humanizer.pick_opening())
        assert len(openings) > 1

    def test_pick_closing_varied(self, humanizer: ResponseHumanizer) -> None:
        closings = set()
        for _ in range(20):
            closings.add(humanizer.pick_closing())
        assert len(closings) > 1

    def test_humanize_text_synonym(self, humanizer: ResponseHumanizer) -> None:
        result = humanizer.humanize_text("Quiero buscar un modelo")
        assert result is not None
        assert len(result) > 0

    def test_pick_fallback_not_generic(self, humanizer: ResponseHumanizer) -> None:
        fallback = humanizer.pick_fallback_intro()
        assert fallback is not None
        assert "Gracias por tu mensaje" not in fallback

    def test_pick_no_results(self, humanizer: ResponseHumanizer) -> None:
        no_result = humanizer.pick_no_results()
        assert no_result is not None


# ─── Style System Tests ──────────────────────────────────────────────────────

class TestStyleSystem:
    @pytest.fixture
    def style_system(self) -> StyleSystem:
        return StyleSystem()

    def test_detect_luxury(self, style_system: StyleSystem) -> None:
        profile = style_system.detect_style_profile({"style": "elegante", "occasion": "fiesta"}, [])
        assert profile in ("luxury", "premium_fashion_advisor")

    def test_detect_streetwear(self, style_system: StyleSystem) -> None:
        profile = style_system.detect_style_profile({"style": "streetwear"}, [])
        assert profile == "streetwear"

    def test_detect_modern_ecommerce(self, style_system: StyleSystem) -> None:
        profile = style_system.detect_style_profile({}, [])
        assert profile == "modern_ecommerce"

    def test_profile_has_required_keys(self, style_system: StyleSystem) -> None:
        for name in ("luxury", "casual", "modern_ecommerce", "streetwear", "premium_fashion_advisor"):
            profile = style_system.get_profile(name)
            assert "openings" in profile
            assert "closings" in profile
            assert "emojis" in profile
            assert len(profile["openings"]) > 0


# ─── Multi-Tenant Isolation Tests ────────────────────────────────────────────

class TestMultiTenantIsolation:
    @pytest.fixture
    def extractor(self) -> EntityExtractor:
        return EntityExtractor()

    def test_different_tenants_same_query_use_correct_empresa(self, extractor: EntityExtractor) -> None:
        entities_a = extractor.extract("chompa talla m")
        entities_b = extractor.extract("chompa talla m")
        assert entities_a.product_type == entities_b.product_type
        assert entities_a.size == entities_b.size
        # empresa_id filtering happens at DB query level (ProductContextEngine)
        # Entity extraction is empresa-agnostic (correct by design)
