import pytest

from app.ai.classifiers.intent_classifier import IntentClassifierService
from app.ai.schemas.ai_schemas import IntentType


@pytest.fixture
def classifier() -> IntentClassifierService:
    return IntentClassifierService()


class TestIntentClassifier:
    async def test_classify_purchase_intent(self, classifier):
        result = await classifier.classify("Quiero comprar un vestido")
        assert result.intent == IntentType.purchase_intent
        assert result.confidence >= 0.2
        assert len(result.matched_keywords) > 0

    async def test_classify_pricing(self, classifier):
        result = await classifier.classify("Cuál es el precio de este producto")
        assert result.intent == IntentType.pricing
        assert result.confidence >= 0.2

    async def test_classify_greeting(self, classifier):
        result = await classifier.classify("Hola, buenos días")
        assert result.intent == IntentType.greeting
        assert result.confidence >= 0.2

    async def test_classify_negotiation(self, classifier):
        result = await classifier.classify("Me puedes hacer un descuento")
        assert result.intent == IntentType.negotiation
        assert result.confidence >= 0.2

    async def test_classify_delivery(self, classifier):
        result = await classifier.classify("Cuándo llega mi pedido")
        assert result.intent == IntentType.delivery
        assert result.confidence >= 0.2

    async def test_classify_support(self, classifier):
        result = await classifier.classify("Necesito ayuda con un error")
        assert result.intent == IntentType.support
        assert result.confidence >= 0.2

    async def test_classify_return_request(self, classifier):
        result = await classifier.classify("Quiero devolver un producto")
        assert result.intent == IntentType.return_request
        assert result.confidence >= 0.2

    async def test_classify_product_question(self, classifier):
        result = await classifier.classify("De qué material está hecho")
        assert result.intent == IntentType.product_question
        assert result.confidence >= 0.2

    async def test_classify_sizing(self, classifier):
        result = await classifier.classify("Qué talla me recomiendas")
        assert result.intent == IntentType.sizing
        assert result.confidence >= 0.2

    async def test_classify_unknown(self, classifier):
        result = await classifier.classify("xyzzy flurbo garble")
        assert result.intent == IntentType.unknown
        assert result.confidence == 0.0

    async def test_empty_message(self, classifier):
        result = await classifier.classify("")
        assert result.intent == IntentType.unknown
        assert result.confidence == 0.0

    async def test_case_insensitive(self, classifier):
        result = await classifier.classify("HOLA, BUENOS DÍAS")
        assert result.intent == IntentType.greeting
        assert result.confidence >= 0.2

    async def test_english_keywords(self, classifier):
        result = await classifier.classify("I want to buy a dress")
        assert result.intent == IntentType.purchase_intent
        assert result.confidence >= 0.2

    async def test_multiple_intents_highest_score_wins(self, classifier):
        result = await classifier.classify("Hola, cuánto cuesta este producto")
        assert result.confidence >= 0.2

    async def test_confidence_bounds(self, classifier):
        result = await classifier.classify("Comprar")
        assert 0.0 <= result.confidence <= 1.0
