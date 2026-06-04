"""Tests for AI Live Conversations module."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest

from app.ai_live.models import ConversationAIEvent, ConversationAIState
from app.ai_live.repository import ConversationAIRepository
from datetime import datetime, timezone

from app.ai_live.schemas import (
    AIStateResponse,
    AnalyzeIntentResponse,
    HandoffResponse,
    SuggestedReply,
)
from app.ai_live.services.handoff_service import HandoffService
from app.ai_live.services.suggestions_service import AISuggestionsService
from tests.conftest import TEST_CONVERSATION_ID, TEST_EMPRESA_ID

TEST_CONVERSATION_ID_2 = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")


@pytest.fixture
def state_model():
    return ConversationAIState(
        id=uuid4(),
        empresa_id=TEST_EMPRESA_ID,
        conversation_id=TEST_CONVERSATION_ID,
        ai_enabled=True,
        auto_reply_enabled=False,
        escalation_required=False,
        last_detected_intent="greeting",
        sentiment="neutral",
        urgency_score=0.3,
        lead_temperature="cold",
        ai_last_response=None,
        ai_confidence=None,
    )


@pytest.fixture
def event_model():
    return ConversationAIEvent(
        id=uuid4(),
        empresa_id=TEST_EMPRESA_ID,
        conversation_id=TEST_CONVERSATION_ID,
        event_type="intent_analyzed",
        payload='{"intent": "greeting"}',
    )


class TestConversationAIRepository:
    async def test_get_or_create_state_creates_new(self, mock_session):
        # After C-2, the repository first verifies the conversation exists
        # in ``conversations_core`` (defensive check). The first SELECT
        # returns a non-None sentinel; the second SELECT (the actual state
        # lookup) returns None, which forces a create path.
        exists_result = MagicMock()
        exists_result.scalar_one_or_none.return_value = TEST_CONVERSATION_ID
        state_result = MagicMock()
        state_result.scalar_one_or_none.return_value = None

        call_count = {"n": 0}

        def side_effect(*args, **kwargs):
            call_count["n"] += 1
            return exists_result if call_count["n"] == 1 else state_result

        mock_session.execute = AsyncMock(side_effect=side_effect)

        repo = ConversationAIRepository(session=mock_session)
        state = await repo.get_or_create_state(
            empresa_id=TEST_EMPRESA_ID, conversation_id=TEST_CONVERSATION_ID
        )

        assert state.empresa_id == TEST_EMPRESA_ID
        assert state.conversation_id == TEST_CONVERSATION_ID
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()

    async def test_get_or_create_state_raises_when_conversation_missing(
        self, mock_session,
    ):
        # C-2: if the conversation does not exist, raise 404 instead of
        # inserting an orphan reference.
        from app.core.errors import AppError

        missing = MagicMock()
        missing.scalar_one_or_none.return_value = None
        mock_session.execute = AsyncMock(return_value=missing)

        repo = ConversationAIRepository(session=mock_session)
        with pytest.raises(AppError) as exc:
            await repo.get_or_create_state(
                empresa_id=TEST_EMPRESA_ID, conversation_id=TEST_CONVERSATION_ID
            )
        assert exc.value.status_code == 404
        assert exc.value.code == "conversation_not_found"
        mock_session.add.assert_not_called()
        mock_session.flush.assert_not_called()

    async def test_get_or_create_state_returns_existing(self, mock_session, state_model):
        # Defensive check returns a sentinel; subsequent lookup returns state.
        exists_result = MagicMock()
        exists_result.scalar_one_or_none.return_value = TEST_CONVERSATION_ID
        state_result = MagicMock()
        state_result.scalar_one_or_none.return_value = state_model

        call_count = {"n": 0}

        def side_effect(*args, **kwargs):
            call_count["n"] += 1
            return exists_result if call_count["n"] == 1 else state_result

        mock_session.execute = AsyncMock(side_effect=side_effect)

        repo = ConversationAIRepository(session=mock_session)
        state = await repo.get_or_create_state(
            empresa_id=TEST_EMPRESA_ID, conversation_id=TEST_CONVERSATION_ID
        )

        assert state is state_model
        mock_session.add.assert_not_called()

    async def test_update_state_fields(self, mock_session, state_model):
        repo = ConversationAIRepository(session=mock_session)
        updated = await repo.update_state(
            state=state_model,
            ai_enabled=False,
            last_detected_intent="purchase_intent",
            urgency_score=0.8,
        )

        assert updated.ai_enabled is False
        assert updated.last_detected_intent == "purchase_intent"
        assert updated.urgency_score == 0.8
        mock_session.flush.assert_called_once()

    async def test_toggle_ai_adds_event(self, mock_session, state_model):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = state_model
        mock_session.execute.return_value = mock_result

        repo = ConversationAIRepository(session=mock_session)
        state = await repo.toggle_ai(
            empresa_id=TEST_EMPRESA_ID,
            conversation_id=TEST_CONVERSATION_ID,
            enabled=False,
        )

        assert state.ai_enabled is False
        mock_session.add.assert_called_once()
        event = mock_session.add.call_args[0][0]
        assert event.event_type == "ai_disabled"

    async def test_toggle_auto_reply(self, mock_session, state_model):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = state_model
        mock_session.execute.return_value = mock_result

        repo = ConversationAIRepository(session=mock_session)
        state = await repo.toggle_auto_reply(
            empresa_id=TEST_EMPRESA_ID,
            conversation_id=TEST_CONVERSATION_ID,
            enabled=True,
        )

        assert state.auto_reply_enabled is True

    async def test_add_event(self, mock_session):
        # C-2: add_event now also runs the defensive conversation check.
        exists_result = MagicMock()
        exists_result.scalar_one_or_none.return_value = TEST_CONVERSATION_ID
        mock_session.execute = AsyncMock(return_value=exists_result)

        repo = ConversationAIRepository(session=mock_session)
        event = await repo.add_event(
            empresa_id=TEST_EMPRESA_ID,
            conversation_id=TEST_CONVERSATION_ID,
            event_type="test_event",
            payload={"key": "value"},
        )
        assert event.event_type == "test_event"
        assert event.empresa_id == TEST_EMPRESA_ID
        assert event.conversation_id == TEST_CONVERSATION_ID
        mock_session.add.assert_called_once()

    async def test_list_events_pagination(self, mock_session, event_model):
        count_result = MagicMock()
        count_result.scalar_one.return_value = 1
        list_result = MagicMock()
        scalars_mock = MagicMock()
        scalars_mock.all.return_value = [event_model]
        list_result.scalars.return_value = scalars_mock

        def execute_side_effect(*args, **kwargs):
            if "count" in str(args[0]):
                return count_result
            return list_result

        mock_session.execute = AsyncMock(side_effect=execute_side_effect)

        repo = ConversationAIRepository(session=mock_session)
        events, total = await repo.list_events(
            empresa_id=TEST_EMPRESA_ID,
            conversation_id=TEST_CONVERSATION_ID,
            limit=10,
            offset=0,
        )

        assert total == 1
        assert len(events) == 1

    async def test_tenant_isolation(self, mock_session, state_model):
        # Defensive check returns sentinel; state lookup returns state_model.
        exists_result = MagicMock()
        exists_result.scalar_one_or_none.return_value = TEST_CONVERSATION_ID
        state_result = MagicMock()
        state_result.scalar_one_or_none.return_value = state_model

        call_count = {"n": 0}

        def side_effect(*args, **kwargs):
            call_count["n"] += 1
            return exists_result if call_count["n"] == 1 else state_result

        mock_session.execute = AsyncMock(side_effect=side_effect)

        repo = ConversationAIRepository(session=mock_session)
        state = await repo.get_or_create_state(
            empresa_id=TEST_EMPRESA_ID, conversation_id=TEST_CONVERSATION_ID
        )

        assert state.empresa_id == TEST_EMPRESA_ID
        assert state.conversation_id == TEST_CONVERSATION_ID


class TestHandoffService:
    @pytest.fixture
    def handoff_service(self):
        return HandoffService()

    async def test_evaluate_escalation_angry_keyword(self, handoff_service):
        shall, reason = await handoff_service.evaluate_escalation(
            empresa_id=TEST_EMPRESA_ID,
            message="Estoy muy molesto con el producto",
            intent="unknown",
            lead_score=0.0,
        )
        assert shall is True
        assert "angry_customer" in reason

    async def test_evaluate_escalation_refund_keyword(self, handoff_service):
        shall, reason = await handoff_service.evaluate_escalation(
            empresa_id=TEST_EMPRESA_ID,
            message="Quiero el reembolso de mi dinero",
            intent="unknown",
            lead_score=0.0,
        )
        assert shall is True
        assert "refund_request" in reason

    async def test_evaluate_escalation_by_intent(self, handoff_service):
        shall, reason = await handoff_service.evaluate_escalation(
            empresa_id=TEST_EMPRESA_ID,
            message="Necesito ayuda",
            intent="complaint",
            lead_score=0.0,
        )
        assert shall is True

    async def test_evaluate_escalation_high_lead_score(self, handoff_service):
        shall, reason = await handoff_service.evaluate_escalation(
            empresa_id=TEST_EMPRESA_ID,
            message="Hola, buen dia",
            intent="greeting",
            lead_score=0.95,
        )
        assert shall is True

    async def test_no_escalation_needed(self, handoff_service):
        shall, reason = await handoff_service.evaluate_escalation(
            empresa_id=TEST_EMPRESA_ID,
            message="Hola, buen dia",
            intent="greeting",
            lead_score=0.0,
        )
        assert shall is False
        assert reason is None

    async def test_escalation_english_keywords(self, handoff_service):
        shall, reason = await handoff_service.evaluate_escalation(
            empresa_id=TEST_EMPRESA_ID,
            message="I am very disappointed with this product",
            intent="unknown",
            lead_score=0.0,
        )
        assert shall is True
        assert "angry_customer" in reason

    async def test_tenant_isolation_respected(self, handoff_service):
        other_empresa = UUID("99999999-9999-4999-8999-999999999999")
        shall, reason = await handoff_service.evaluate_escalation(
            empresa_id=other_empresa,
            message="Estoy molesto",
            intent="unknown",
            lead_score=0.0,
        )
        assert shall is True
        assert "angry_customer" in reason


class TestAISuggestionsService:
    @pytest.fixture
    def mock_repo(self, state_model):
        repo = AsyncMock()
        repo.get_or_create_state.return_value = state_model
        return repo

    @pytest.fixture
    def mock_llm(self):
        llm = AsyncMock()
        llm.generate.return_value = "Gracias por contactarnos, ¿cómo podemos ayudarte?"
        return llm

    @pytest.fixture
    def mock_handoff(self):
        return AsyncMock()

    def test_template_suggestions_returns_list(self, mock_repo, mock_llm, mock_handoff):
        service = AISuggestionsService(
            repository=mock_repo,
            llm_service=mock_llm,
            handoff_service=mock_handoff,
        )
        suggestions = service._template_suggestions("greeting", "Hola")
        assert len(suggestions) >= 1
        assert suggestions[0].text
        assert suggestions[0].confidence == 0.75

    def test_template_suggestions_unknown_intent(self, mock_repo, mock_llm, mock_handoff):
        service = AISuggestionsService(
            repository=mock_repo,
            llm_service=mock_llm,
            handoff_service=mock_handoff,
        )
        suggestions = service._template_suggestions("unknown_intent", "test")
        assert len(suggestions) == 3

    def test_fallback_suggestions(self, mock_repo, mock_llm, mock_handoff):
        service = AISuggestionsService(
            repository=mock_repo,
            llm_service=mock_llm,
            handoff_service=mock_handoff,
        )
        suggestions = service._fallback_suggestions()
        assert len(suggestions) == 1
        assert suggestions[0].confidence == 0.5


class TestSchemas:
    def test_ai_state_response_valid(self):
        response = AIStateResponse(
            id=uuid4(),
            empresa_id=TEST_EMPRESA_ID,
            conversation_id=TEST_CONVERSATION_ID,
            ai_enabled=True,
            auto_reply_enabled=False,
            escalation_required=False,
            last_detected_intent="greeting",
            sentiment="neutral",
            urgency_score=0.3,
            lead_temperature="cold",
            ai_last_response=None,
            ai_confidence=None,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        assert response.ai_enabled is True
        assert response.conversation_id == TEST_CONVERSATION_ID

    def test_suggested_reply_valid(self):
        reply = SuggestedReply(text="Hello", confidence=0.9, reasoning="test")
        assert reply.text == "Hello"
        assert reply.confidence == 0.9

    def test_suggested_reply_confidence_range(self):
        with pytest.raises(Exception):
            SuggestedReply(text="test", confidence=1.5, reasoning="test")

    def test_handoff_response(self):
        response = HandoffResponse(success=True, message="Done")
        assert response.success is True

    def test_analyze_intent_response(self):
        response = AnalyzeIntentResponse(
            detected_intent="purchase_intent",
            sentiment="positive",
            urgency_score=0.8,
            lead_temperature="hot",
            confidence=0.95,
        )
        assert response.detected_intent == "purchase_intent"
        assert response.confidence == 0.95
