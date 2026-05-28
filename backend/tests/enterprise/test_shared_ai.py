from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import pytest

from app.ai.schemas.ai_schemas import IntentType, SalesAction, ConversationStage
from app.shared_ai.conversation_adapter import ConversationAdapter
from app.shared_ai.unified_intent_service import UnifiedIntentService, UnifiedIntentType
from app.shared_ai.unified_rules_engine import UnifiedRulesEngine


class TestUnifiedIntentService:
    def test_service_creation(self):
        service = UnifiedIntentService()
        assert service is not None

    async def test_to_unified_accepts_strings(self):
        service = UnifiedIntentService()
        result = service.to_unified("purchase_intent")
        assert isinstance(result, UnifiedIntentType)
        assert result == UnifiedIntentType.purchase

    async def test_to_unified_accepts_ai_enum(self):
        service = UnifiedIntentService()
        result = service.to_unified(IntentType.purchase_intent)
        assert result == UnifiedIntentType.purchase

    async def test_to_unified_unknown_string(self):
        service = UnifiedIntentService()
        result = service.to_unified("nonexistent_intent")
        assert result == UnifiedIntentType.unknown

    async def test_to_ai_type_conversion(self):
        service = UnifiedIntentService()
        result = service.to_ai_type(UnifiedIntentType.purchase)
        assert result == IntentType.purchase_intent

    async def test_to_sales_type_conversion(self):
        service = UnifiedIntentService()
        from app.sales.intents.intent import IntentType as SalesIntentType
        result = service.to_sales_type(UnifiedIntentType.purchase)
        assert result == SalesIntentType.purchase_intent

    async def test_classify_unified(self):
        service = UnifiedIntentService()
        with patch.object(service._ai_classifier, "classify", AsyncMock(return_value=MagicMock(intent=IntentType.purchase_intent, confidence=0.85))):
            intent, confidence = await service.classify_unified("Quiero comprar")
            assert intent == UnifiedIntentType.purchase
            assert confidence == 0.85

    async def test_classify_unified_sync(self):
        service = UnifiedIntentService()
        with patch.object(service._sales_classifier, "classify", return_value=(MagicMock(value="purchase_intent"), 5)):
            intent, weight = service.classify_unified_sync("Quiero comprar")
            assert isinstance(intent, UnifiedIntentType)

    async def test_empty_input_handling(self):
        service = UnifiedIntentService()
        result = service.to_unified("")
        assert result == UnifiedIntentType.unknown


class TestUnifiedRulesEngine:
    def test_engine_creation(self):
        engine = UnifiedRulesEngine()
        assert engine is not None

    async def test_evaluate_ai_action_with_ai_intent(self):
        engine = UnifiedRulesEngine()
        action = await engine.evaluate_ai_action(
            empresa_id=UUID("00000000-0000-0000-0000-000000000001"),
            intent=IntentType.purchase_intent,
            stage=ConversationStage.active,
            lead_score=0.8,
            message_count=5,
        )
        assert isinstance(action, SalesAction)

    async def test_evaluate_ai_action_with_unified_intent(self):
        engine = UnifiedRulesEngine()
        action = await engine.evaluate_ai_action(
            empresa_id=UUID("00000000-0000-0000-0000-000000000001"),
            intent=UnifiedIntentType.purchase,
            stage=ConversationStage.active,
            lead_score=0.8,
            message_count=5,
        )
        assert isinstance(action, SalesAction)

    async def test_evaluate_ai_action_low_lead_score(self):
        engine = UnifiedRulesEngine()
        action = await engine.evaluate_ai_action(
            empresa_id=UUID("00000000-0000-0000-0000-000000000001"),
            intent=IntentType.purchase_intent,
            stage=ConversationStage.active,
            lead_score=0.1,
            message_count=1,
        )
        assert isinstance(action, SalesAction)

    async def test_evaluate_ai_action_with_return_request(self):
        engine = UnifiedRulesEngine()
        action = await engine.evaluate_ai_action(
            empresa_id=UUID("00000000-0000-0000-0000-000000000001"),
            intent=IntentType.return_request,
            stage=ConversationStage.active,
            lead_score=0.0,
            message_count=1,
        )
        assert action == SalesAction.escalate


class TestConversationAdapter:
    def test_adapter_creation(self):
        session = AsyncMock()
        adapter = ConversationAdapter(session)
        assert adapter is not None

    async def test_adapter_type_unknown(self):
        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        session.execute = AsyncMock(return_value=mock_result)
        adapter = ConversationAdapter(session)
        result = await adapter.get_adapter_type(
            empresa_id=UUID("00000000-0000-0000-0000-000000000001"),
            conversation_id=UUID("00000000-0000-0000-0000-000000000003"),
        )
        assert result == "unknown"
