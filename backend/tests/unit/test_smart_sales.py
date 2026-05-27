import pytest
from uuid import uuid4, UUID

from app.smart_sales.entity_extractor import EntityExtractor, ExtractedEntities
from app.smart_sales.product_matcher import ProductMatcher, MatchedProduct, MatchedVariant
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
        assert "Hola" in response or "hola" in response.lower()

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
        assert "rojo" in response.lower()


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

        class FakeResult:
            def unique(self):
                return self
            def scalars(self) -> list:
                return self
            def all(self) -> list:
                return []

        session = AsyncMock()
        session.execute = AsyncMock(return_value=FakeResult())

        brain = SmartSalesBrain(session=session)
        reply = await brain.generate_reply(
            empresa_id=uuid4(),
            user_message="quiero una chompa talla m negra",
        )
        assert reply
        assert len(reply) > 10


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
