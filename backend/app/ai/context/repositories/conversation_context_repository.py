import logging
from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_live.models import ConversationAIEvent, ConversationAIState
from app.conversations.models import ConversationCore, MessageCore
from app.modules.conversations.models import Conversation, Message

logger = logging.getLogger("ai_sales_agent.ai.context.repositories.conversation")


class ConversationContextRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_conversation_core(
        self, *, empresa_id: UUID, conversation_id: UUID
    ) -> ConversationCore | None:
        result = await self._session.execute(
            select(ConversationCore).where(
                ConversationCore.empresa_id == empresa_id,
                ConversationCore.id == conversation_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_conversation_module(
        self, *, empresa_id: UUID, conversation_id: UUID
    ) -> Conversation | None:
        result = await self._session.execute(
            select(Conversation).where(
                Conversation.empresa_id == empresa_id,
                Conversation.id == conversation_id,
                Conversation.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def get_recent_messages_core(
        self, *, empresa_id: UUID, conversation_id: UUID, limit: int = 20
    ) -> list[dict]:
        result = await self._session.execute(
            select(MessageCore)
            .where(
                MessageCore.empresa_id == empresa_id,
                MessageCore.conversation_id == conversation_id,
            )
            .order_by(MessageCore.created_at.desc())
            .limit(limit)
        )
        messages: Sequence[MessageCore] = result.scalars().all()
        return [
            {
                "id": str(m.id),
                "sender": m.sender,
                "content": m.content,
                "created_at": m.created_at,
            }
            for m in reversed(messages)
        ]

    async def get_recent_messages_module(
        self, *, empresa_id: UUID, conversation_id: UUID, limit: int = 20
    ) -> list[dict]:
        result = await self._session.execute(
            select(Message)
            .where(
                Message.empresa_id == empresa_id,
                Message.conversation_id == conversation_id,
            )
            .order_by(Message.created_at.desc())
            .limit(limit)
        )
        messages: Sequence[Message] = result.scalars().all()
        return [
            {
                "id": str(m.id),
                "role": m.role,
                "content": m.content,
                "sender_name": m.sender_name,
                "created_at": m.created_at,
            }
            for m in reversed(messages)
        ]

    async def get_ai_state(
        self, *, empresa_id: UUID, conversation_id: UUID
    ) -> ConversationAIState | None:
        result = await self._session.execute(
            select(ConversationAIState).where(
                ConversationAIState.empresa_id == empresa_id,
                ConversationAIState.conversation_id == conversation_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_ai_events(
        self, *, empresa_id: UUID, conversation_id: UUID, limit: int = 50
    ) -> list[ConversationAIEvent]:
        result = await self._session.execute(
            select(ConversationAIEvent)
            .where(
                ConversationAIEvent.empresa_id == empresa_id,
                ConversationAIEvent.conversation_id == conversation_id,
            )
            .order_by(ConversationAIEvent.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def has_escalations(
        self, *, empresa_id: UUID, conversation_id: UUID
    ) -> bool:
        state = await self.get_ai_state(
            empresa_id=empresa_id, conversation_id=conversation_id
        )
        if state and state.escalation_required:
            return True
        events = await self.get_ai_events(
            empresa_id=empresa_id, conversation_id=conversation_id, limit=100
        )
        return any(e.event_type in ("escalation", "handoff_requested", "ai_response_escalated") for e in events)

    async def get_detected_intents(
        self, *, empresa_id: UUID, conversation_id: UUID
    ) -> list[str]:
        state = await self.get_ai_state(
            empresa_id=empresa_id, conversation_id=conversation_id
        )
        intents = []
        if state and state.last_detected_intent:
            intents.append(state.last_detected_intent)
        events = await self.get_ai_events(
            empresa_id=empresa_id, conversation_id=conversation_id, limit=100
        )
        for e in events:
            if e.event_type == "suggestion_generated" and e.payload:
                import json
                try:
                    data = json.loads(e.payload)
                    if isinstance(data, dict) and data.get("intent"):
                        intents.append(data["intent"])
                except (json.JSONDecodeError, TypeError):
                    pass
        seen = set()
        return [i for i in intents if i not in seen and not seen.add(i)]

    async def get_sentiment_history(
        self, *, empresa_id: UUID, conversation_id: UUID
    ) -> list[str]:
        state = await self.get_ai_state(
            empresa_id=empresa_id, conversation_id=conversation_id
        )
        sentiments = []
        if state and state.sentiment:
            sentiments.append(state.sentiment)
        events = await self.get_ai_events(
            empresa_id=empresa_id, conversation_id=conversation_id, limit=100
        )
        for e in events:
            if e.event_type in ("sentiment_update", "ai_analysis") and e.payload:
                import json
                try:
                    data = json.loads(e.payload)
                    if isinstance(data, dict) and data.get("sentiment"):
                        sentiments.append(data["sentiment"])
                except (json.JSONDecodeError, TypeError):
                    pass
        return sentiments

    async def compute_average_response_time(
        self, *, empresa_id: UUID, conversation_id: UUID
    ) -> float:
        messages = await self.get_recent_messages_core(
            empresa_id=empresa_id, conversation_id=conversation_id, limit=50
        )
        if len(messages) < 2:
            return 0.0
        response_diffs = []
        for i in range(1, len(messages)):
            prev = messages[i - 1]
            curr = messages[i]
            if prev.get("created_at") and curr.get("created_at"):
                diff = (curr["created_at"] - prev["created_at"]).total_seconds() / 60
                if 0 < diff < 1440:
                    response_diffs.append(diff)
        if not response_diffs:
            return 0.0
        return sum(response_diffs) / len(response_diffs)
