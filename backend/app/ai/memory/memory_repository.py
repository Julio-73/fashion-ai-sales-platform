import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.memory.models import ConversationMemory

logger = logging.getLogger("ai_sales_agent.ai.memory.repository")


class MemoryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_memories_by_customer(
        self, *, empresa_id: UUID, customer_id: UUID
    ) -> list[ConversationMemory]:
        result = await self._session.execute(
            select(ConversationMemory)
            .where(
                ConversationMemory.empresa_id == empresa_id,
                ConversationMemory.customer_id == customer_id,
            )
            .order_by(ConversationMemory.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_memory_by_type(
        self, *, empresa_id: UUID, customer_id: UUID, memory_type: str
    ) -> ConversationMemory | None:
        result = await self._session.execute(
            select(ConversationMemory)
            .where(
                ConversationMemory.empresa_id == empresa_id,
                ConversationMemory.customer_id == customer_id,
                ConversationMemory.memory_type == memory_type,
            )
        )
        return result.scalar_one_or_none()

    async def upsert_memory(
        self,
        *,
        empresa_id: UUID,
        customer_id: UUID,
        conversation_id: UUID | None = None,
        memory_type: str = "general",
        summary: str | None = None,
        extracted_preferences: list[str] | None = None,
        extracted_sizes: list[str] | None = None,
        extracted_colors: list[str] | None = None,
        extracted_styles: list[str] | None = None,
        extracted_occasions: list[str] | None = None,
        confidence: float = 0.5,
    ) -> ConversationMemory:
        existing = await self.get_memory_by_type(
            empresa_id=empresa_id,
            customer_id=customer_id,
            memory_type=memory_type,
        )
        if existing:
            existing.summary = summary or existing.summary
            existing.conversation_id = conversation_id or existing.conversation_id
            existing.confidence = max(confidence, existing.confidence)
            if extracted_preferences is not None:
                existing.extracted_preferences = self._merge_lists(existing.extracted_preferences, extracted_preferences)
            if extracted_sizes is not None:
                existing.extracted_sizes = self._merge_lists(existing.extracted_sizes, extracted_sizes)
            if extracted_colors is not None:
                existing.extracted_colors = self._merge_lists(existing.extracted_colors, extracted_colors)
            if extracted_styles is not None:
                existing.extracted_styles = self._merge_lists(existing.extracted_styles, extracted_styles)
            if extracted_occasions is not None:
                existing.extracted_occasions = self._merge_lists(existing.extracted_occasions, extracted_occasions)
            await self._session.flush()
            return existing

        memory = ConversationMemory(
            empresa_id=empresa_id,
            customer_id=customer_id,
            conversation_id=conversation_id,
            memory_type=memory_type,
            summary=summary,
            extracted_preferences=extracted_preferences,
            extracted_sizes=extracted_sizes,
            extracted_colors=extracted_colors,
            extracted_styles=extracted_styles,
            extracted_occasions=extracted_occasions,
            confidence=confidence,
        )
        self._session.add(memory)
        await self._session.flush()
        return memory

    async def delete_memory(
        self, *, memory: ConversationMemory
    ) -> None:
        await self._session.delete(memory)
        await self._session.flush()

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()

    def _merge_lists(self, existing: list[str] | None, new: list[str]) -> list[str]:
        existing_set = set(existing or [])
        existing_set.update(new)
        return sorted(existing_set)
