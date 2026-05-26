from uuid import UUID

import pytest
from pydantic import ValidationError

from app.ai.schemas.ai_schemas import (
    ClassifyRequest,
    ContextRequest,
    IntentClassification,
    IntentType,
    OrchestratorRequest,
    OrchestratorResponse,
    SalesAction,
    ReplyType,
)


class TestClassifyRequest:
    def test_valid_request(self):
        req = ClassifyRequest(message="Hola", empresa_id=UUID(int=1))
        assert req.message == "Hola"

    def test_empty_message_raises(self):
        with pytest.raises(ValidationError):
            ClassifyRequest(message="", empresa_id=UUID(int=1))

    def test_message_too_long_raises(self):
        with pytest.raises(ValidationError):
            ClassifyRequest(message="x" * 5001, empresa_id=UUID(int=1))


class TestContextRequest:
    def test_valid_request(self):
        req = ContextRequest(
            empresa_id=UUID(int=1),
            customer_id=UUID(int=2),
            conversation_id=UUID(int=3),
        )
        assert req.empresa_id == UUID(int=1)
        assert req.customer_id == UUID(int=2)
        assert req.conversation_id == UUID(int=3)


class TestOrchestratorRequest:
    def test_valid_request(self):
        req = OrchestratorRequest(
            message="Hola",
            empresa_id=UUID(int=1),
            customer_id=UUID(int=2),
            conversation_id=UUID(int=3),
        )
        assert req.message == "Hola"

    def test_empty_message_raises(self):
        with pytest.raises(ValidationError):
            OrchestratorRequest(
                message="",
                empresa_id=UUID(int=1),
                customer_id=UUID(int=2),
                conversation_id=UUID(int=3),
            )


class TestIntentClassification:
    def test_default_matched_keywords(self):
        ic = IntentClassification(intent=IntentType.greeting, confidence=0.9)
        assert ic.matched_keywords == []

    def test_with_keywords(self):
        ic = IntentClassification(
            intent=IntentType.pricing,
            confidence=0.8,
            matched_keywords=["precio", "cuesta"],
        )
        assert len(ic.matched_keywords) == 2

    def test_confidence_bounds(self):
        with pytest.raises(ValidationError):
            IntentClassification(intent=IntentType.greeting, confidence=1.5)
        with pytest.raises(ValidationError):
            IntentClassification(intent=IntentType.greeting, confidence=-0.1)

    def test_zero_confidence_valid(self):
        ic = IntentClassification(intent=IntentType.unknown, confidence=0.0)
        assert ic.confidence == 0.0


class TestOrchestratorResponse:
    def test_default_values(self):
        resp = OrchestratorResponse(
            intent=IntentType.greeting,
            intent_confidence=0.9,
            sales_action=SalesAction.no_action,
            should_reply=True,
            reply_type=ReplyType.greeting,
        )
        assert resp.generated_response == ""
        assert resp.recommended_product_ids == []
        assert resp.suggested_discount_pct is None
        assert resp.escalate_reason is None

    def test_full_response(self):
        pid = UUID(int=999)
        resp = OrchestratorResponse(
            intent=IntentType.purchase_intent,
            intent_confidence=0.95,
            sales_action=SalesAction.suggest_upsell,
            should_reply=True,
            reply_type=ReplyType.sales,
            generated_response="Great choice!",
            recommended_product_ids=[pid],
            suggested_discount_pct=15.0,
            escalate_reason=None,
        )
        assert resp.intent_confidence == 0.95
        assert resp.recommended_product_ids == [pid]
        assert resp.suggested_discount_pct == 15.0

    def test_confidence_bounds(self):
        with pytest.raises(ValidationError):
            OrchestratorResponse(
                intent=IntentType.greeting,
                intent_confidence=2.0,
                sales_action=SalesAction.no_action,
                should_reply=False,
                reply_type=ReplyType.no_reply,
            )
