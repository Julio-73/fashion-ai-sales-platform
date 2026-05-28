from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.memory.memory_repository import MemoryRepository
from app.ai.memory.memory_summarizer import MemorySummarizer
from app.ai.memory.models import ConversationMemory
from app.ai.memory.persistent_memory_service import PersistentMemoryService
from app.ai.schemas.ai_schemas import RichContextData, RichCustomerProfile


def _mock_execute_result(data=None):
    """Create a MagicMock that mimics SQLAlchemy execute result.

    Use with: session.execute = AsyncMock(return_value=_mock_execute_result(...))
    so that await session.execute(...) returns this result.
    """
    result = MagicMock()
    result.scalars.return_value.all.return_value = data or []
    result.scalar_one_or_none.return_value = None
    result.scalar_one.return_value = None
    return result


@pytest.fixture
def mock_session():
    session = MagicMock(spec=AsyncSession)
    mock_result = _mock_execute_result()
    session.execute = AsyncMock(return_value=mock_result)
    session.add = MagicMock()
    session.add_all = MagicMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = MagicMock()
    session.delete = AsyncMock()
    session.rollback = AsyncMock()
    return session


class TestMemoryRepository:
    EMPRESA_ID = UUID("00000000-0000-0000-0000-000000000001")
    CUSTOMER_ID = UUID("00000000-0000-0000-0000-000000000002")

    def test_repo_creation(self, mock_session):
        repo = MemoryRepository(mock_session)
        assert repo is not None

    async def test_upsert_creates_new_memory(self, mock_session):
        repo = MemoryRepository(mock_session)
        mock_result = _mock_execute_result()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)

        memory = await repo.upsert_memory(
            empresa_id=self.EMPRESA_ID,
            customer_id=self.CUSTOMER_ID,
            memory_type="test_type",
            summary="Test summary",
            extracted_colors=["rojo", "negro"],
            extracted_sizes=["M"],
            confidence=0.8,
        )

        assert mock_session.add.called
        assert mock_session.flush.called

    async def test_upsert_updates_existing_memory(self, mock_session):
        repo = MemoryRepository(mock_session)
        existing = MagicMock(spec=ConversationMemory)
        existing.extracted_colors = ["azul"]
        existing.extracted_sizes = ["S"]
        existing.extracted_styles = None
        existing.extracted_occasions = None
        existing.extracted_preferences = None
        existing.confidence = 0.5
        existing.summary = "Old"
        mock_result = _mock_execute_result()
        mock_result.scalar_one_or_none.return_value = existing
        mock_session.execute = AsyncMock(return_value=mock_result)

        memory = await repo.upsert_memory(
            empresa_id=self.EMPRESA_ID,
            customer_id=self.CUSTOMER_ID,
            memory_type="test_type",
            summary="Updated summary",
            extracted_colors=["rojo"],
            extracted_sizes=["M"],
            confidence=0.9,
        )

        assert existing.summary == "Updated summary"
        assert existing.confidence == 0.9
        assert "rojo" in existing.extracted_colors

    async def test_get_memories_by_customer(self, mock_session):
        repo = MemoryRepository(mock_session)
        mock_memory = MagicMock(spec=ConversationMemory)
        mock_result = _mock_execute_result([mock_memory])
        mock_session.execute = AsyncMock(return_value=mock_result)

        memories = await repo.get_memories_by_customer(
            empresa_id=self.EMPRESA_ID, customer_id=self.CUSTOMER_ID
        )

        assert len(memories) == 1
        assert mock_session.execute.called

    async def test_delete_memory(self, mock_session):
        repo = MemoryRepository(mock_session)
        mock_memory = MagicMock(spec=ConversationMemory)
        await repo.delete_memory(memory=mock_memory)
        assert mock_session.delete.called
        assert mock_session.flush.called

    async def test_commit(self, mock_session):
        repo = MemoryRepository(mock_session)
        await repo.commit()
        assert mock_session.commit.called

    async def test_rollback(self, mock_session):
        repo = MemoryRepository(mock_session)
        await repo.rollback()
        assert mock_session.rollback.called


class TestMemorySummarizer:
    def test_summarizer_creation(self):
        summarizer = MemorySummarizer()
        assert summarizer is not None

    async def test_summarize_messages_with_entities(self):
        summarizer = MemorySummarizer()
        messages = [
            {"content": "Quiero un vestido rojo talla M", "role": "client"},
            {"content": "Me gusta el estilo elegante", "role": "client"},
        ]
        result = await summarizer.summarize_messages(messages)
        assert "summary" in result
        assert len(result["colors"]) > 0
        assert len(result["sizes"]) > 0

    async def test_summarize_empty_messages(self):
        summarizer = MemorySummarizer()
        result = await summarizer.summarize_messages([])
        assert result["summary"] == "Sin resumen disponible"
        assert result["confidence"] == 0.3

    def test_summarize_memory_context(self):
        summarizer = MemorySummarizer()
        result = summarizer.summarize_memory_context(
            preferences=["interesado en vestidos"],
            colors=["rojo", "negro"],
            sizes=["M"],
            styles=["elegante"],
        )
        assert "rojo" in result
        assert "elegante" in result
        assert "interesado en vestidos" in result

    def test_summarize_memory_context_empty(self):
        summarizer = MemorySummarizer()
        result = summarizer.summarize_memory_context(
            preferences=[], colors=[], sizes=[], styles=[]
        )
        assert "Sin preferencias registradas" in result


class TestPersistentMemoryService:
    EMPRESA_ID = UUID("00000000-0000-0000-0000-000000000001")
    CUSTOMER_ID = UUID("00000000-0000-0000-0000-000000000002")
    CONVERSATION_ID = UUID("00000000-0000-0000-0000-000000000003")

    def test_service_creation(self, mock_session):
        service = PersistentMemoryService(mock_session)
        assert service is not None
        assert service._in_memory is not None

    async def test_get_memories_for_prompt_without_data(self, mock_session):
        mock_session.execute = AsyncMock(return_value=_mock_execute_result([]))
        service = PersistentMemoryService(mock_session)

        result = await service.get_memories_for_prompt(
            empresa_id=self.EMPRESA_ID, customer_id=self.CUSTOMER_ID
        )

        assert "Sin historial" in result

    async def test_store_memory_from_messages(self, mock_session):
        mock_result = _mock_execute_result()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)
        service = PersistentMemoryService(mock_session)

        messages = [
            {"content": "Me gusta la ropa negra talla M", "role": "client"},
        ]
        result = await service.store_memory_from_messages(
            empresa_id=self.EMPRESA_ID,
            customer_id=self.CUSTOMER_ID,
            conversation_id=self.CONVERSATION_ID,
            messages=messages,
        )

        assert "memory_id" in result
        assert "summary" in result

    async def test_clear_conversation_memory(self, mock_session):
        service = PersistentMemoryService(mock_session)
        await service.clear_conversation_memory(self.CONVERSATION_ID)
        assert True
