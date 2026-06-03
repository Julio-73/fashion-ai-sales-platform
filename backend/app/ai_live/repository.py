import json
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_live.models import ConversationAIEvent, ConversationAIState


class ConversationAIRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_or_create_state(
        self, *, empresa_id: UUID, conversation_id: UUID,
    ) -> ConversationAIState:
        result = await self._session.execute(
            select(ConversationAIState).where(
                ConversationAIState.empresa_id == empresa_id,
                ConversationAIState.conversation_id == conversation_id,
            )
        )
        state = result.scalar_one_or_none()
        if state is None:
            state = ConversationAIState(
                empresa_id=empresa_id,
                conversation_id=conversation_id,
            )
            self._session.add(state)
            await self._session.flush()
            await self._session.refresh(state)
        return state

    async def update_state(
        self,
        *,
        state: ConversationAIState,
        ai_enabled: bool | None = None,
        auto_reply_enabled: bool | None = None,
        escalation_required: bool | None = None,
        last_detected_intent: str | None = None,
        sentiment: str | None = None,
        urgency_score: float | None = None,
        lead_temperature: str | None = None,
        ai_last_response: str | None = None,
        ai_confidence: float | None = None,
    ) -> ConversationAIState:
        if ai_enabled is not None:
            state.ai_enabled = ai_enabled
        if auto_reply_enabled is not None:
            state.auto_reply_enabled = auto_reply_enabled
        if escalation_required is not None:
            state.escalation_required = escalation_required
        if last_detected_intent is not None:
            state.last_detected_intent = last_detected_intent
        if sentiment is not None:
            state.sentiment = sentiment
        if urgency_score is not None:
            state.urgency_score = urgency_score
        if lead_temperature is not None:
            state.lead_temperature = lead_temperature
        if ai_last_response is not None:
            state.ai_last_response = ai_last_response
        if ai_confidence is not None:
            state.ai_confidence = ai_confidence
        await self._session.flush()
        return state

    async def toggle_ai(self, *, empresa_id: UUID, conversation_id: UUID, enabled: bool) -> ConversationAIState:
        state = await self.get_or_create_state(empresa_id=empresa_id, conversation_id=conversation_id)
        state.ai_enabled = enabled
        await self._session.flush()
        await self._session.refresh(state)
        await self.add_event(
            empresa_id=empresa_id,
            conversation_id=conversation_id,
            event_type="ai_enabled" if enabled else "ai_disabled",
        )
        return state

    async def toggle_auto_reply(self, *, empresa_id: UUID, conversation_id: UUID, enabled: bool) -> ConversationAIState:
        state = await self.get_or_create_state(empresa_id=empresa_id, conversation_id=conversation_id)
        state.auto_reply_enabled = enabled
        await self._session.flush()
        await self._session.refresh(state)
        return state

    async def add_event(
        self,
        *,
        empresa_id: UUID,
        conversation_id: UUID,
        event_type: str,
        payload: dict | None = None,
    ) -> ConversationAIEvent:
        event = ConversationAIEvent(
            empresa_id=empresa_id,
            conversation_id=conversation_id,
            event_type=event_type,
            payload=json.dumps(payload) if payload else None,
        )
        self._session.add(event)
        await self._session.flush()
        return event

    async def list_events(
        self,
        *,
        empresa_id: UUID,
        conversation_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[ConversationAIEvent], int]:
        query = select(ConversationAIEvent).where(
            ConversationAIEvent.empresa_id == empresa_id,
            ConversationAIEvent.conversation_id == conversation_id,
        )
        count_result = await self._session.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = int(count_result.scalar_one())
        result = await self._session.execute(
            query.order_by(ConversationAIEvent.created_at.desc())
            .limit(limit).offset(offset)
        )
        return list(result.scalars().all()), total

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()
