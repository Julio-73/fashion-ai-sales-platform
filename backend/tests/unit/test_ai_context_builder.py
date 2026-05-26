from uuid import UUID

import pytest

from app.ai.context.context_builder import ConversationContextBuilder
from app.ai.schemas.ai_schemas import ConversationStage


@pytest.fixture
def builder() -> ConversationContextBuilder:
    return ConversationContextBuilder()


class TestConversationContextBuilder:
    async def test_build_returns_context_response(self, builder):
        empresa_id = UUID("00000000-0000-0000-0000-000000000001")
        customer_id = UUID("00000000-0000-0000-0000-000000000002")
        conversation_id = UUID("00000000-0000-0000-0000-000000000003")

        result = await builder.build(
            empresa_id=empresa_id,
            customer_id=customer_id,
            conversation_id=conversation_id,
        )

        assert result.context.customer.customer_id == customer_id
        assert result.context.customer.lead_score == 0.0
        assert result.context.customer.tags == []
        assert result.context.recent_messages == []
        assert result.context.product_interests == []

    async def test_new_conversation_stage(self, builder):
        empresa_id = UUID("00000000-0000-0000-0000-000000000001")
        customer_id = UUID("00000000-0000-0000-0000-000000000002")
        conversation_id = UUID("00000000-0000-0000-0000-000000000003")

        result = await builder.build(
            empresa_id=empresa_id,
            customer_id=customer_id,
            conversation_id=conversation_id,
        )

        assert result.context.conversation_stage == ConversationStage.new

    async def test_tenant_isolation_by_empresa_id(self, builder):
        id_a = UUID("00000000-0000-0000-0000-000000000001")
        id_b = UUID("00000000-0000-0000-0000-00000000000a")

        result_a = await builder.build(
            empresa_id=id_a,
            customer_id=id_a,
            conversation_id=id_a,
        )
        result_b = await builder.build(
            empresa_id=id_b,
            customer_id=id_b,
            conversation_id=id_b,
        )

        assert result_a.context.customer.customer_id != result_b.context.customer.customer_id
        assert result_a.context.customer.customer_id == id_a
        assert result_b.context.customer.customer_id == id_b
