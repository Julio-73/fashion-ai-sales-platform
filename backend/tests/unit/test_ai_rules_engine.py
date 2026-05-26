from uuid import UUID

import pytest

from app.ai.rules.sales_rules import SalesConversationRulesEngine
from app.ai.schemas.ai_schemas import ConversationStage, IntentType, SalesAction


@pytest.fixture
def engine() -> SalesConversationRulesEngine:
    return SalesConversationRulesEngine()


class TestSalesConversationRulesEngine:
    EMPRESA_ID = UUID("00000000-0000-0000-0000-000000000001")
    STAGE = ConversationStage.active

    async def test_return_request_escalates(self, engine):
        action = await engine.evaluate(
            empresa_id=self.EMPRESA_ID,
            intent=IntentType.return_request,
            stage=self.STAGE,
            lead_score=0.5,
            message_count=1,
        )
        assert action == SalesAction.escalate

    async def test_low_score_with_multiple_messages_follows_up(self, engine):
        action = await engine.evaluate(
            empresa_id=self.EMPRESA_ID,
            intent=IntentType.pricing,
            stage=self.STAGE,
            lead_score=0.1,
            message_count=3,
        )
        assert action == SalesAction.follow_up

    async def test_negotiation_high_score_suggests_discount(self, engine):
        action = await engine.evaluate(
            empresa_id=self.EMPRESA_ID,
            intent=IntentType.negotiation,
            stage=self.STAGE,
            lead_score=0.7,
            message_count=2,
        )
        assert action == SalesAction.suggest_discount

    async def test_high_score_active_suggests_upsell(self, engine):
        action = await engine.evaluate(
            empresa_id=self.EMPRESA_ID,
            intent=IntentType.pricing,
            stage=ConversationStage.active,
            lead_score=0.85,
            message_count=3,
        )
        assert action == SalesAction.suggest_upsell

    async def test_purchase_intent_medium_score_suggests_cross_sell(self, engine):
        action = await engine.evaluate(
            empresa_id=self.EMPRESA_ID,
            intent=IntentType.purchase_intent,
            stage=self.STAGE,
            lead_score=0.6,
            message_count=2,
        )
        assert action == SalesAction.suggest_cross_sell

    async def test_very_high_score_long_conversation_escalates(self, engine):
        action = await engine.evaluate(
            empresa_id=self.EMPRESA_ID,
            intent=IntentType.pricing,
            stage=self.STAGE,
            lead_score=0.75,
            message_count=6,
        )
        assert action == SalesAction.escalate

    async def test_no_action_when_nothing_matches(self, engine):
        action = await engine.evaluate(
            empresa_id=self.EMPRESA_ID,
            intent=IntentType.greeting,
            stage=self.STAGE,
            lead_score=0.3,
            message_count=1,
        )
        assert action == SalesAction.no_action

    async def test_tenant_isolation(self, engine):
        action_a = await engine.evaluate(
            empresa_id=UUID("00000000-0000-0000-0000-000000000001"),
            intent=IntentType.return_request,
            stage=self.STAGE,
            lead_score=0.5,
            message_count=1,
        )
        action_b = await engine.evaluate(
            empresa_id=UUID("00000000-0000-0000-0000-000000000002"),
            intent=IntentType.greeting,
            stage=self.STAGE,
            lead_score=0.3,
            message_count=1,
        )
        assert action_a == SalesAction.escalate
        assert action_b == SalesAction.no_action
