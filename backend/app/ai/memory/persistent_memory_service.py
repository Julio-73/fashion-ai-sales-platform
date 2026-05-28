import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.memory.memory_repository import MemoryRepository
from app.ai.memory.memory_summarizer import MemorySummarizer
from app.smart_sales.memory.conversation_memory import ConversationMemoryManager

logger = logging.getLogger("ai_sales_agent.ai.memory.persistent_service")


class PersistentMemoryService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = MemoryRepository(session)
        self._summarizer = MemorySummarizer()
        self._in_memory = ConversationMemoryManager()

    async def get_or_create_context(self, conversation_id: UUID | str):
        return self._in_memory.get_or_create(conversation_id)

    async def store_memory_from_messages(
        self,
        *,
        empresa_id: UUID,
        customer_id: UUID,
        conversation_id: UUID,
        messages: list[dict],
    ) -> dict:
        summary_data = await self._summarizer.summarize_messages(messages)
        memory = await self._repo.upsert_memory(
            empresa_id=empresa_id,
            customer_id=customer_id,
            conversation_id=conversation_id,
            memory_type="conversation_summary",
            summary=summary_data["summary"],
            extracted_preferences=summary_data["preferences"],
            extracted_sizes=summary_data["sizes"],
            extracted_colors=summary_data["colors"],
            extracted_styles=summary_data["styles"],
            extracted_occasions=summary_data["occasions"],
            confidence=summary_data["confidence"],
        )
        await self._repo.commit()
        return {
            "memory_id": str(memory.id),
            "summary": memory.summary or "",
            "colors": memory.extracted_colors or [],
            "sizes": memory.extracted_sizes or [],
            "styles": memory.extracted_styles or [],
            "confidence": memory.confidence,
        }

    async def get_customer_memory_summary(
        self,
        *,
        empresa_id: UUID,
        customer_id: UUID,
    ) -> str:
        memories = await self._repo.get_memories_by_customer(
            empresa_id=empresa_id, customer_id=customer_id
        )
        if not memories:
            return "Sin historial previo con este cliente."
        all_prefs = []
        all_colors = set()
        all_sizes = set()
        all_styles = set()
        for m in memories:
            if m.extracted_preferences:
                all_prefs.extend(m.extracted_preferences)
            if m.extracted_colors:
                all_colors.update(m.extracted_colors)
            if m.extracted_sizes:
                all_sizes.update(m.extracted_sizes)
            if m.extracted_styles:
                all_styles.update(m.extracted_styles)
        return self._summarizer.summarize_memory_context(
            preferences=all_prefs,
            colors=list(all_colors),
            sizes=list(all_sizes),
            styles=list(all_styles),
        )

    async def get_memories_for_prompt(
        self,
        *,
        empresa_id: UUID,
        customer_id: UUID,
    ) -> str:
        summary = await self.get_customer_memory_summary(
            empresa_id=empresa_id, customer_id=customer_id
        )
        return summary

    async def clear_conversation_memory(self, conversation_id: UUID | str) -> None:
        self._in_memory.clear(conversation_id)
