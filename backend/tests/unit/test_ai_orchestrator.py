from uuid import UUID

import pytest

from app.ai.orchestrators.response_orchestrator import AIResponseOrchestrator
from app.ai.orchestrators.response_templates import ResponseTemplateBuilder
from app.ai.schemas.ai_schemas import (
    IntentType,
    OrchestratorRequest,
    ReplyType,
    SalesAction,
)


@pytest.fixture
def orchestrator() -> AIResponseOrchestrator:
    return AIResponseOrchestrator()


class TestAIResponseOrchestrator:
    EMPRESA_ID = UUID("00000000-0000-0000-0000-000000000001")
    CUSTOMER_ID = UUID("00000000-0000-0000-0000-000000000002")
    CONVERSATION_ID = UUID("00000000-0000-0000-0000-000000000003")

    async def test_orchestrate_greeting(self, orchestrator):
        request = OrchestratorRequest(
            message="Hola, buenos días",
            empresa_id=self.EMPRESA_ID,
            customer_id=self.CUSTOMER_ID,
            conversation_id=self.CONVERSATION_ID,
        )
        result = await orchestrator.orchestrate(request)
        assert result.intent == IntentType.greeting
        assert result.should_reply is True
        assert result.reply_type == ReplyType.greeting
        assert len(result.generated_response) > 0

    async def test_orchestrate_purchase_intent(self, orchestrator):
        request = OrchestratorRequest(
            message="Quiero comprar un vestido",
            empresa_id=self.EMPRESA_ID,
            customer_id=self.CUSTOMER_ID,
            conversation_id=self.CONVERSATION_ID,
        )
        result = await orchestrator.orchestrate(request)
        assert result.intent == IntentType.purchase_intent
        assert result.should_reply is True
        assert result.reply_type == ReplyType.sales

    async def test_orchestrate_return_request_escalates(self, orchestrator):
        request = OrchestratorRequest(
            message="Quiero devolver un producto",
            empresa_id=self.EMPRESA_ID,
            customer_id=self.CUSTOMER_ID,
            conversation_id=self.CONVERSATION_ID,
        )
        result = await orchestrator.orchestrate(request)
        assert result.intent == IntentType.return_request
        assert result.sales_action == SalesAction.escalate
        assert result.reply_type == ReplyType.escalation
        assert result.escalate_reason is not None

    async def test_orchestrate_unknown_does_not_reply(self, orchestrator):
        request = OrchestratorRequest(
            message="xyzzy flurbo garble",
            empresa_id=self.EMPRESA_ID,
            customer_id=self.CUSTOMER_ID,
            conversation_id=self.CONVERSATION_ID,
        )
        result = await orchestrator.orchestrate(request)
        assert result.intent == IntentType.unknown
        assert result.should_reply is False
        assert result.reply_type == ReplyType.no_reply
        assert result.sales_action == SalesAction.no_action

    async def test_confidence_in_response(self, orchestrator):
        request = OrchestratorRequest(
            message="Hola",
            empresa_id=self.EMPRESA_ID,
            customer_id=self.CUSTOMER_ID,
            conversation_id=self.CONVERSATION_ID,
        )
        result = await orchestrator.orchestrate(request)
        assert 0.0 <= result.intent_confidence <= 1.0

    async def test_generated_response_not_empty_for_known_intents(self, orchestrator):
        for msg, expected_intent in [
            ("Hola", IntentType.greeting),
            ("Cuánto cuesta", IntentType.pricing),
            ("Quiero comprar", IntentType.purchase_intent),
            ("Necesito ayuda", IntentType.support),
        ]:
            request = OrchestratorRequest(
                message=msg,
                empresa_id=self.EMPRESA_ID,
                customer_id=self.CUSTOMER_ID,
                conversation_id=self.CONVERSATION_ID,
            )
            result = await orchestrator.orchestrate(request)
            assert result.intent == expected_intent
            if result.should_reply:
                assert len(result.generated_response) > 0, f"No response for {msg}"


class TestResponseTemplateBuilder:
    def test_sales_template_exists_for_all_intents(self):
        for intent in IntentType:
            template = ResponseTemplateBuilder.build_sales_response(intent)
            if intent != IntentType.unknown:
                assert isinstance(template, str)

    def test_reply_type_mapping(self):
        assert ResponseTemplateBuilder.get_reply_type(IntentType.support) == ReplyType.support
        assert ResponseTemplateBuilder.get_reply_type(IntentType.greeting) == ReplyType.greeting
        assert ResponseTemplateBuilder.get_reply_type(IntentType.pricing) == ReplyType.sales
        assert ResponseTemplateBuilder.get_reply_type(IntentType.return_request) == ReplyType.escalation
        assert ResponseTemplateBuilder.get_reply_type(IntentType.unknown) == ReplyType.no_reply

    def test_follow_up_template(self):
        result = ResponseTemplateBuilder.build_follow_up("Test")
        assert "Test" in result
        assert ResponseTemplateBuilder.build_follow_up() is not None
