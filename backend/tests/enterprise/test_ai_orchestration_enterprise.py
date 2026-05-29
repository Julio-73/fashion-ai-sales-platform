from unittest.mock import AsyncMock, patch
from uuid import UUID

import pytest

from app.ai.schemas.ai_schemas import (
    ConversationHistory,
    ConversationStage,
    IntentType,
    OrchestratorRequest,
    OrchestratorResponse,
    ProductContextDetail,
    ReplyType,
    RichContextData,
    RichCustomerProfile,
    SalesAction,
    SalesContextDetail,
)
from app.ai.services.ai_service import AIService


class TestAIOrchestrationEnterprise:
    EMPRESA_ID = UUID("00000000-0000-0000-0000-000000000001")
    CUSTOMER_ID = UUID("00000000-0000-0000-0000-000000000002")
    CONVERSATION_ID = UUID("00000000-0000-0000-0000-000000000003")

    async def test_respond_works_with_rich_context(self):
        service = AIService(session=AsyncMock())

        request = OrchestratorRequest(
            message="Hola, quiero comprar un vestido rojo",
            empresa_id=self.EMPRESA_ID,
            customer_id=self.CUSTOMER_ID,
            conversation_id=self.CONVERSATION_ID,
        )

        with patch.object(service._orchestrator, "orchestrate", AsyncMock(return_value=OrchestratorResponse(
            intent=IntentType.purchase_intent,
            intent_confidence=0.85,
            sales_action=SalesAction.suggest_upsell,
            should_reply=True,
            reply_type=ReplyType.sales,
            generated_response="Te recomiendo nuestro vestido rojo premium.",
        ))), patch.object(service._real_context_builder, "build_rich_context", AsyncMock(return_value=RichContextData(
            customer=RichCustomerProfile(
                customer_id=self.CUSTOMER_ID,
                full_name="Test User",
                lead_score=0.0,
                tags=[],
            ),
            conversation=ConversationHistory(),
            products=ProductContextDetail(),
            sales=SalesContextDetail(),
        ))):
            result = await service.respond(request)

        assert result.intent == IntentType.purchase_intent
        assert result.generated_response != ""
        assert result.should_reply is True

    async def test_rich_context_includes_orchestrator_response(self):
        service = AIService(session=AsyncMock())

        request = OrchestratorRequest(
            message="Quiero devolver un producto",
            empresa_id=self.EMPRESA_ID,
            customer_id=self.CUSTOMER_ID,
            conversation_id=self.CONVERSATION_ID,
        )

        with patch.object(service._real_context_builder, "build_rich_context", AsyncMock(return_value=RichContextData(
            customer=RichCustomerProfile(
                customer_id=self.CUSTOMER_ID,
                full_name="Test",
                lead_score=0.0,
                tags=[],
            ),
            conversation=ConversationHistory(),
            products=ProductContextDetail(),
            sales=SalesContextDetail(),
        ))):
            result = await service.respond(request)

        assert result.rich_context is not None or result.sales_action is not None
        assert result.sales_action == SalesAction.escalate

    async def test_rich_context_fallback_on_error(self):
        service = AIService(session=AsyncMock())

        def fail_build(*args, **kwargs):
            raise RuntimeError("DB connection error")

        service._real_context_builder.build_rich_context = fail_build

        request = OrchestratorRequest(
            message="Hola",
            empresa_id=self.EMPRESA_ID,
            customer_id=self.CUSTOMER_ID,
            conversation_id=self.CONVERSATION_ID,
        )

        result = await service.respond(request)

        assert result is not None
        assert result.intent == IntentType.greeting
        assert result.should_reply is True
        assert result.generated_response != ""

    async def test_orchestrator_accepts_rich_context_param(self):
        from app.ai.orchestrators.response_orchestrator import AIResponseOrchestrator

        orchestrator = AIResponseOrchestrator()

        request = OrchestratorRequest(
            message="Hola",
            empresa_id=self.EMPRESA_ID,
            customer_id=self.CUSTOMER_ID,
            conversation_id=self.CONVERSATION_ID,
        )

        rich = RichContextData(
            customer=RichCustomerProfile(
                customer_id=self.CUSTOMER_ID,
                full_name="Rich Client",
                lead_score=90.0,
                tags=["vip"],
            ),
            conversation=ConversationHistory(total_messages=5),
            products=ProductContextDetail(),
            sales=SalesContextDetail(),
        )

        result = await orchestrator.orchestrate(request, rich_context=rich)

        assert result.intent == IntentType.greeting
        assert result.rich_context is not None

    async def test_rich_context_does_not_break_existing_behavior(self):
        from app.ai.orchestrators.response_orchestrator import AIResponseOrchestrator

        orchestrator = AIResponseOrchestrator()

        request = OrchestratorRequest(
            message="xyzzy flurbo",
            empresa_id=self.EMPRESA_ID,
            customer_id=self.CUSTOMER_ID,
            conversation_id=self.CONVERSATION_ID,
        )

        result_no_rich = await orchestrator.orchestrate(request)
        result_with_rich = await orchestrator.orchestrate(request, rich_context=None)

        assert result_no_rich.intent == IntentType.unknown
        assert result_no_rich.should_reply is False
        assert result_with_rich.intent == IntentType.unknown
        assert result_with_rich.should_reply is False
