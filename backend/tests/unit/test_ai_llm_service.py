from unittest.mock import AsyncMock, patch
from uuid import UUID

import pytest

from app.ai.config import AISettings
from app.ai.providers.openai_provider import OpenAIProvider, OpenAIProviderError
from app.ai.schemas.ai_schemas import (
    ContextData,
    ConversationStage,
    CustomerProfileRef,
    IntentType,
    SalesAction,
)
from app.ai.services.llm_service import LLMService, PromptComposer


@pytest.fixture
def unconfigured_llm_service() -> LLMService:
    settings = AISettings(openai_api_key="")
    return LLMService(settings=settings)


@pytest.fixture
def configured_llm_service() -> LLMService:
    settings = AISettings(
        openai_api_key="sk-test",
        openai_model="gpt-4o-mini",
    )
    provider = OpenAIProvider(settings=settings)
    return LLMService(provider=provider, settings=settings)


@pytest.fixture
def sample_context() -> ContextData:
    return ContextData(
        customer=CustomerProfileRef(
            customer_id=UUID("00000000-0000-0000-0000-000000000001"),
            customer_name="Cliente Test",
            lead_score=0.8,
            tags=["vip", "recurrente"],
        ),
        recent_messages=["Hola, quiero información", "Me interesa el vestido rojo"],
        conversation_stage=ConversationStage.active,
        product_interests=["Vestido rojo", "Zapatos"],
    )


@pytest.fixture
def empresa_id() -> UUID:
    return UUID("00000000-0000-0000-0000-00000000000a")


class TestPromptComposer:
    def test_compose_sales_prompt(self):
        result = PromptComposer.compose(
            intent=IntentType.pricing,
            sales_action=SalesAction.no_action,
            customer_name="Cliente Test",
            product_interests=["Vestido"],
            conversation_history=["Hola"],
            lead_score=0.5,
            conversation_stage="active",
            user_message="Cuánto cuesta el vestido",
        )
        assert "Cliente Test" in result
        assert "Cuánto cuesta el vestido" in result
        assert "Vestido" in result
        assert "Eres un asistente de ventas" in result or "Eres un" in result

    def test_compose_negotiation_prompt(self):
        result = PromptComposer.compose(
            intent=IntentType.negotiation,
            sales_action=SalesAction.suggest_discount,
            customer_name="Test",
            product_interests=["Producto"],
            conversation_history=[],
            lead_score=0.7,
            conversation_stage="active",
            user_message="Me puedes hacer descuento",
        )
        assert "Me puedes hacer descuento" in result
        assert "negociador" in result.lower() or "negociación" in result.lower() or "negoci" in result.lower()

    def test_compose_upsell_prompt(self):
        result = PromptComposer.compose(
            intent=IntentType.pricing,
            sales_action=SalesAction.suggest_upsell,
            customer_name="Test",
            product_interests=["Vestido"],
            conversation_history=[],
            lead_score=0.9,
            conversation_stage="closing",
            user_message="Quiero el vestido básico",
        )
        assert "Quiero el vestido básico" in result
        assert "upselling" in result.lower() or "upgrade" in result.lower() or "calidad" in result.lower()

    def test_compose_support_prompt(self):
        result = PromptComposer.compose(
            intent=IntentType.support,
            sales_action=SalesAction.no_action,
            customer_name="Test",
            product_interests=[],
            conversation_history=[],
            lead_score=0.3,
            conversation_stage="active",
            user_message="Necesito ayuda",
        )
        assert "Necesito ayuda" in result
        assert "soporte" in result.lower()

    def test_compose_recovery_prompt(self):
        result = PromptComposer.compose(
            intent=IntentType.pricing,
            sales_action=SalesAction.follow_up,
            customer_name="Test",
            product_interests=["Producto"],
            conversation_history=[],
            lead_score=0.2,
            conversation_stage="new",
            user_message="Hola",
        )
        assert "Hola" in result
        assert "recuperación" in result.lower() or "ventas" in result.lower()

    def test_context_vars_always_provided(self):
        result = PromptComposer.compose(
            intent=IntentType.greeting,
            sales_action=SalesAction.no_action,
            customer_name="",
            product_interests=[],
            conversation_history=[],
            lead_score=0.0,
            conversation_stage="new",
            user_message="Hola",
        )
        assert "Hola" in result
        assert "cliente" in result.lower()


class TestLLMService:
    async def test_not_configured_returns_fallback(self, unconfigured_llm_service, sample_context, empresa_id):
        result = await unconfigured_llm_service.generate_response(
            empresa_id=empresa_id,
            intent=IntentType.pricing,
            sales_action=SalesAction.no_action,
            context=sample_context,
            user_message="Cuánto cuesta?",
        )
        assert result == unconfigured_llm_service._fallback_response
        assert "agente humano" in result

    @pytest.mark.asyncio
    async def test_configured_calls_provider(self, configured_llm_service, sample_context, empresa_id):
        mock_generate = AsyncMock(return_value="Respuesta generada por IA")
        with patch.object(configured_llm_service._provider, "generate", mock_generate):
            result = await configured_llm_service.generate_response(
                empresa_id=empresa_id,
                intent=IntentType.pricing,
                sales_action=SalesAction.no_action,
                context=sample_context,
                user_message="Cuánto cuesta?",
            )

        assert result == "Respuesta generada por IA"
        mock_generate.assert_called_once()

    @pytest.mark.asyncio
    async def test_fallback_on_provider_error(self, configured_llm_service, sample_context, empresa_id):
        mock_generate = AsyncMock(side_effect=OpenAIProviderError("API error"))
        with patch.object(configured_llm_service._provider, "generate", mock_generate):
            result = await configured_llm_service.generate_response(
                empresa_id=empresa_id,
                intent=IntentType.pricing,
                sales_action=SalesAction.no_action,
                context=sample_context,
                user_message="Cuánto cuesta?",
            )

        assert result == configured_llm_service._fallback_response

    @pytest.mark.asyncio
    async def test_fallback_on_unexpected_error(self, configured_llm_service, sample_context, empresa_id):
        mock_generate = AsyncMock(side_effect=RuntimeError("Unexpected"))
        with patch.object(configured_llm_service._provider, "generate", mock_generate):
            result = await configured_llm_service.generate_response(
                empresa_id=empresa_id,
                intent=IntentType.pricing,
                sales_action=SalesAction.no_action,
                context=sample_context,
                user_message="Cuánto cuesta?",
            )

        assert result == configured_llm_service._fallback_response

    @pytest.mark.asyncio
    async def test_is_configured_property(self):
        unconfig = LLMService(settings=AISettings(openai_api_key=""))
        assert unconfig.is_configured is False

        config = LLMService(settings=AISettings(openai_api_key="sk-test"))
        assert config.is_configured is True

    @pytest.mark.asyncio
    async def test_different_empresa_ids_flow_through(self):
        settings = AISettings(openai_api_key="sk-test")
        provider = OpenAIProvider(settings=settings)
        service = LLMService(provider=provider, settings=settings)

        context_a = ContextData(
            customer=CustomerProfileRef(
                customer_id=UUID("00000000-0000-0000-0000-000000000001"),
                customer_name="Cliente A",
                lead_score=0.5,
                tags=[],
            ),
            recent_messages=[],
            conversation_stage=ConversationStage.new,
            product_interests=[],
        )

        context_b = ContextData(
            customer=CustomerProfileRef(
                customer_id=UUID("00000000-0000-0000-0000-000000000002"),
                customer_name="Cliente B",
                lead_score=0.9,
                tags=[],
            ),
            recent_messages=[],
            conversation_stage=ConversationStage.new,
            product_interests=[],
        )

        empresa_a = UUID("00000000-0000-0000-0000-00000000000a")
        empresa_b = UUID("00000000-0000-0000-0000-00000000000b")

        mock_gen = AsyncMock(return_value="OK")
        with patch.object(provider, "generate", mock_gen):
            await service.generate_response(
                empresa_id=empresa_a,
                intent=IntentType.pricing,
                sales_action=SalesAction.no_action,
                context=context_a,
                user_message="Msg A",
            )
            await service.generate_response(
                empresa_id=empresa_b,
                intent=IntentType.negotiation,
                sales_action=SalesAction.suggest_discount,
                context=context_b,
                user_message="Msg B",
            )

        assert mock_gen.call_count == 2

        call_1_user_msg = mock_gen.call_args_list[0][1]["user_message"]
        call_2_user_msg = mock_gen.call_args_list[1][1]["user_message"]
        assert call_1_user_msg == "Msg A"
        assert call_2_user_msg == "Msg B"


class TestLLMServiceOrchestratorIntegration:
    @pytest.mark.asyncio
    async def test_orchestrator_falls_back_to_templates_without_llm(self):
        from app.ai.orchestrators.response_orchestrator import AIResponseOrchestrator
        from app.ai.schemas.ai_schemas import OrchestratorRequest

        orchestrator = AIResponseOrchestrator()
        request = OrchestratorRequest(
            message="Hola, buenos días",
            empresa_id=UUID("00000000-0000-0000-0000-000000000001"),
            customer_id=UUID("00000000-0000-0000-0000-000000000002"),
            conversation_id=UUID("00000000-0000-0000-0000-000000000003"),
        )

        result = await orchestrator.orchestrate(request)
        assert result.intent == IntentType.greeting
        assert result.generated_response != ""
        assert result.should_reply is True

    @pytest.mark.asyncio
    async def test_orchestrator_uses_llm_when_configured(self):
        from app.ai.orchestrators.response_orchestrator import AIResponseOrchestrator
        from app.ai.schemas.ai_schemas import OrchestratorRequest

        settings = AISettings(openai_api_key="sk-test")
        provider = OpenAIProvider(settings=settings)
        llm_service = LLMService(provider=provider, settings=settings)

        orchestrator = AIResponseOrchestrator(llm_service=llm_service)

        request = OrchestratorRequest(
            message="Quiero comprar un vestido",
            empresa_id=UUID("00000000-0000-0000-0000-000000000001"),
            customer_id=UUID("00000000-0000-0000-0000-000000000002"),
            conversation_id=UUID("00000000-0000-0000-0000-000000000003"),
        )

        llm_response = "Te recomiendo nuestro vestido rojo que está en oferta."

        mock_gen = AsyncMock(return_value=llm_response)
        with patch.object(provider, "generate", mock_gen):
            result = await orchestrator.orchestrate(request)

        assert result.generated_response == llm_response
        assert result.intent == IntentType.purchase_intent

    @pytest.mark.asyncio
    async def test_orchestrator_escalate_goes_directly_no_llm(self):
        from app.ai.orchestrators.response_orchestrator import AIResponseOrchestrator
        from app.ai.schemas.ai_schemas import OrchestratorRequest, ReplyType

        settings = AISettings(openai_api_key="sk-test")
        provider = OpenAIProvider(settings=settings)
        llm_service = LLMService(provider=provider, settings=settings)

        orchestrator = AIResponseOrchestrator(llm_service=llm_service)

        request = OrchestratorRequest(
            message="Quiero devolver un producto",
            empresa_id=UUID("00000000-0000-0000-0000-000000000001"),
            customer_id=UUID("00000000-0000-0000-0000-000000000002"),
            conversation_id=UUID("00000000-0000-0000-0000-000000000003"),
        )

        mock_gen = AsyncMock(return_value="No debería llamarse")
        with patch.object(provider, "generate", mock_gen):
            result = await orchestrator.orchestrate(request)

        assert result.sales_action == SalesAction.escalate
        assert result.reply_type == ReplyType.escalation
        assert "agente humano" in result.generated_response.lower() or "derivada" in result.generated_response.lower()
