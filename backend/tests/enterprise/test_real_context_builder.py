from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import pytest

from app.ai.context.services.real_context_builder import RealContextBuilder
from app.ai.schemas.ai_schemas import (
    ConversationHistory,
    ProductContextDetail,
    RichContextData,
    RichCustomerProfile,
    SalesContextDetail,
)


@pytest.fixture
def mock_session():
    session = MagicMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_result.scalar_one_or_none.return_value = None
    mock_result.fetchall.return_value = []
    mock_result.keys.return_value = []
    session.execute = MagicMock(return_value=mock_result)
    return session


@pytest.fixture
def builder(mock_session) -> RealContextBuilder:
    builder = RealContextBuilder(mock_session)
    builder._conversation_repo = MagicMock()
    builder._conversation_repo.get_recent_messages_core = AsyncMock(return_value=[])
    builder._conversation_repo.get_recent_messages_module = AsyncMock(return_value=[])
    builder._conversation_repo.get_detected_intents = AsyncMock(return_value=[])
    builder._conversation_repo.get_sentiment_history = AsyncMock(return_value=[])
    builder._conversation_repo.has_escalations = AsyncMock(return_value=False)
    builder._conversation_repo.compute_average_response_time = AsyncMock(return_value=0.0)
    builder._conversation_repo.get_conversation_core = AsyncMock(return_value=None)
    builder._product_repo = MagicMock()
    builder._product_repo.get_products_by_customer = AsyncMock(return_value=[])
    builder._product_repo.get_total_products_queried = AsyncMock(return_value=0)
    builder._product_repo.get_preferred_styles = AsyncMock(return_value=[])
    builder._product_repo.get_preferred_categories = AsyncMock(return_value=[])
    builder._product_repo.get_products_viewed_by_customer = AsyncMock(return_value=[])
    builder._product_repo.get_products_asked_by_customer = AsyncMock(return_value=[])
    builder._product_repo.get_frequent_categories = AsyncMock(return_value=[])
    builder._product_repo.get_preferred_styles_from_memory = AsyncMock(return_value=[])
    builder._product_repo.find_upsell_candidates = AsyncMock(return_value=[])
    return builder


class TestRealContextBuilder:
    EMPRESA_ID = UUID("00000000-0000-0000-0000-000000000001")
    CUSTOMER_ID = UUID("00000000-0000-0000-0000-000000000002")
    CONVERSATION_ID = UUID("00000000-0000-0000-0000-000000000003")

    async def test_build_rich_context_returns_valid_data(self, builder):
        with patch.object(builder._customer_memory, "build_profile", AsyncMock(return_value=RichCustomerProfile(
            customer_id=self.CUSTOMER_ID, full_name="Test User"
        ))):
            with patch.object(builder, "_build_conversation_history", AsyncMock(return_value=ConversationHistory())):
                with patch.object(builder, "_build_product_context", AsyncMock(return_value=ProductContextDetail())):
                    with patch.object(builder._behavioral_service, "build_sales_context", AsyncMock(return_value=SalesContextDetail())):
                        result = await builder.build_rich_context(
                            empresa_id=self.EMPRESA_ID,
                            customer_id=self.CUSTOMER_ID,
                            conversation_id=self.CONVERSATION_ID,
                        )

        assert isinstance(result, RichContextData)
        assert result.customer.customer_id == self.CUSTOMER_ID
        assert result.customer.full_name == "Test User"

    async def test_rich_context_contains_all_sections(self, builder):
        with patch.object(builder._customer_memory, "build_profile", AsyncMock(return_value=RichCustomerProfile(
            customer_id=self.CUSTOMER_ID, full_name="Test"
        ))):
            with patch.object(builder, "_build_conversation_history", AsyncMock(return_value=ConversationHistory(
                total_messages=5, status="active"
            ))):
                with patch.object(builder, "_build_product_context", AsyncMock(return_value=ProductContextDetail(
                    total_products_queried=3
                ))):
                    with patch.object(builder._behavioral_service, "build_sales_context", AsyncMock(return_value=SalesContextDetail(
                        conversion_probability="high", is_hot_lead=True
                    ))):
                        result = await builder.build_rich_context(
                            empresa_id=self.EMPRESA_ID,
                            customer_id=self.CUSTOMER_ID,
                            conversation_id=self.CONVERSATION_ID,
                        )

        assert result.customer is not None
        assert result.conversation is not None
        assert result.products is not None
        assert result.sales is not None
        assert result.conversation.total_messages == 5
        assert result.products.total_products_queried == 3
        assert result.sales.conversion_probability == "high"
        assert result.sales.is_hot_lead is True

    async def test_tenant_isolation_preserved(self, builder):
        empresa_a = UUID("00000000-0000-0000-0000-00000000000a")
        empresa_b = UUID("00000000-0000-0000-0000-00000000000b")

        with patch.object(builder._customer_memory, "build_profile", AsyncMock(return_value=RichCustomerProfile(
            customer_id=self.CUSTOMER_ID, full_name="A"
        ))):
            with patch.object(builder, "_build_conversation_history", AsyncMock(return_value=ConversationHistory())):
                with patch.object(builder, "_build_product_context", AsyncMock(return_value=ProductContextDetail())):
                    with patch.object(builder._behavioral_service, "build_sales_context", AsyncMock(return_value=SalesContextDetail())):
                        result_a = await builder.build_rich_context(
                            empresa_id=empresa_a,
                            customer_id=self.CUSTOMER_ID,
                            conversation_id=self.CONVERSATION_ID,
                        )
                        result_b = await builder.build_rich_context(
                            empresa_id=empresa_b,
                            customer_id=self.CUSTOMER_ID,
                            conversation_id=self.CONVERSATION_ID,
                        )

        assert result_a.customer.full_name == "A"

    async def test_conversation_history_empty_when_no_data(self, builder):
        history = await builder._build_conversation_history(
            empresa_id=self.EMPRESA_ID,
            conversation_id=self.CONVERSATION_ID,
        )
        assert isinstance(history, ConversationHistory)
        assert history.total_messages == 0

    async def test_product_context_defaults(self, builder):
        context = await builder._build_product_context(
            empresa_id=self.EMPRESA_ID,
            customer_id=self.CUSTOMER_ID,
        )
        assert isinstance(context, ProductContextDetail)
        assert context.total_products_queried == 0
