from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import pytest

from app.ai.context.services.customer_memory_service import CustomerMemoryService
from app.ai.memory.memory_repository import MemoryRepository


def _mock_execute_result(data=None):
    result = MagicMock()
    result.scalars.return_value.all.return_value = data or []
    result.scalar_one_or_none.return_value = None
    result.scalar_one.return_value = None
    return result


class TestTenantIsolation:
    """Enterprise-critical: verify data isolation between tenants."""

    EMPRESA_A = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
    EMPRESA_B = UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb")
    CUSTOMER_A = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1")
    CUSTOMER_B = UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbb1")

    def test_repositories_accept_empresa_id(self):
        """All context repositories must accept empresa_id as a parameter."""
        from app.ai.context.repositories.customer_context_repository import (
            CustomerContextRepository,
        )
        from app.ai.context.repositories.conversation_context_repository import (
            ConversationContextRepository,
        )
        from app.ai.context.repositories.product_context_repository import (
            ProductContextRepository,
        )
        from app.ai.context.repositories.sales_context_repository import (
            SalesContextRepository,
        )

        session = MagicMock()

        for repo_cls in [
            CustomerContextRepository,
            ConversationContextRepository,
            ProductContextRepository,
            SalesContextRepository,
        ]:
            repo = repo_cls(session)
            methods = [
                m for m in dir(repo)
                if not m.startswith("_") and callable(getattr(repo, m))
            ]
            for method_name in methods:
                method = getattr(repo, method_name)
                import inspect
                sig = inspect.signature(method)
                params = list(sig.parameters.keys())
                if method_name != "commit" and method_name != "rollback":
                    assert "empresa_id" in params, (
                        f"{repo_cls.__name__}.{method_name} missing empresa_id parameter"
                    )

    async def test_memory_repository_tenant_filter(self):
        """MemoryRepository must filter by empresa_id in all queries."""
        session = MagicMock()
        mock_result = _mock_execute_result([])
        session.execute = AsyncMock(return_value=mock_result)
        repo = MemoryRepository(session)

        mock_memory = MagicMock()
        mock_memory.empresa_id = self.EMPRESA_A
        mock_result.scalars.return_value.all.return_value = [mock_memory]

        memories_a = await repo.get_memories_by_customer(
            empresa_id=self.EMPRESA_A,
            customer_id=self.CUSTOMER_A,
        )
        assert len(memories_a) == 1

        call_kwargs = session.execute.call_args[0][0]
        whereclause = str(call_kwargs.whereclause) if hasattr(call_kwargs, 'whereclause') else str(call_kwargs)
        assert str(self.EMPRESA_A) in whereclause or "empresa_id" in whereclause

    def test_customer_memory_service_tenant_aware(self):
        """CustomerMemoryService must require empresa_id."""
        service = CustomerMemoryService(MagicMock())

        import inspect
        sig = inspect.signature(service.build_profile)
        assert "empresa_id" in sig.parameters

        sig = inspect.signature(service.get_customer_tags)
        assert "empresa_id" in sig.parameters

    def test_shared_ai_tenant_aware(self):
        """UnifiedRulesEngine evaluate_ai_action must require empresa_id."""
        from app.shared_ai.unified_rules_engine import UnifiedRulesEngine

        engine = UnifiedRulesEngine()
        import inspect
        sig = inspect.signature(engine.evaluate_ai_action)
        assert "empresa_id" in sig.parameters
