import time
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import pytest


def _mock_execute_result(data=None):
    result = MagicMock()
    result.scalars.return_value.all.return_value = data or []
    result.scalar_one_or_none.return_value = None
    result.scalar_one.return_value = None
    return result


class TestPerformanceValidation:
    """Ensure new code paths do not introduce significant latency."""

    async def test_memory_upsert_is_fast(self):
        from app.ai.memory.memory_repository import MemoryRepository

        session = MagicMock()
        mock_result = _mock_execute_result()
        mock_result.scalar_one_or_none.return_value = None
        session.execute = AsyncMock(return_value=mock_result)
        session.add = MagicMock()
        session.flush = AsyncMock()
        repo = MemoryRepository(session)

        start = time.monotonic()
        for _ in range(50):
            await repo.upsert_memory(
                empresa_id=UUID("00000000-0000-0000-0000-000000000001"),
                customer_id=UUID("00000000-0000-0000-0000-000000000002"),
                memory_type="test",
                summary="test",
            )
        elapsed = time.monotonic() - start
        assert elapsed < 5.0, f"50 upserts took {elapsed:.2f}s (threshold: 5s)"

    async def test_behavior_analyzer_batch_is_fast(self):
        from app.ai.intelligence.customer_behavior_analyzer import (
            CustomerBehaviorAnalyzer,
        )

        session = MagicMock()
        analyzer = CustomerBehaviorAnalyzer(session)

        ids = [UUID(f"00000000-0000-0000-0000-{i:012d}") for i in range(20)]

        with patch.object(analyzer._sales_repo, "is_hot_lead", AsyncMock(return_value=True)):
            with patch.object(analyzer._sales_repo, "get_buying_intent_trend", AsyncMock(return_value="stable")):
                with patch.object(analyzer._sales_repo, "get_conversion_probability", AsyncMock(return_value="medium")):
                    start = time.monotonic()
                    result = await analyzer.detect_hot_customers(
                        empresa_id=UUID("00000000-0000-0000-0000-000000000001"),
                        customer_ids=ids,
                    )
                    elapsed = time.monotonic() - start
                    assert elapsed < 5.0, f"Batch of 20 took {elapsed:.2f}s (threshold: 5s)"
                    assert len(result) == 20

    async def test_prompt_composition_is_fast(self):
        from app.ai.schemas.ai_schemas import (
            ConversationHistory,
            ProductContextDetail,
            RichContextData,
            RichCustomerProfile,
            SalesContextDetail,
        )
        from app.ai.services.llm_service import PromptComposer

        rich = RichContextData(
            customer=RichCustomerProfile(
                customer_id=UUID("00000000-0000-0000-0000-000000000001"),
                full_name="Test User",
                tags=["vip"],
                lead_score=80.0,
                is_vip=True,
                preferred_colors=["rojo", "negro"],
                preferred_sizes=["M"],
                total_conversations=10,
                average_order_value=200.0,
            ),
            conversation=ConversationHistory(total_messages=20),
            products=ProductContextDetail(preferred_styles=["elegante"]),
            sales=SalesContextDetail(conversion_probability="high"),
        )

        start = time.monotonic()
        for _ in range(100):
            PromptComposer.compose(
                intent=MagicMock(),
                sales_action=MagicMock(),
                customer_name="Test",
                product_interests=["Vestido"],
                conversation_history=["Msg1", "Msg2"],
                lead_score=80.0,
                conversation_stage="active",
                user_message="Hola",
                rich_context=rich,
            )
        elapsed = time.monotonic() - start
        assert elapsed < 3.0, f"100 compositions took {elapsed:.2f}s (threshold: 3s)"
