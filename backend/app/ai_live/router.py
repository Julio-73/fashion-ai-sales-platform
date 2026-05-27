from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.ai_live.dependencies import get_ai_live_repository, get_ai_insights_service, get_ai_suggestions_service, get_handoff_service
from app.ai_live.repository import ConversationAIRepository
from app.ai_live.schemas import (
    AIEventListResponse,
    AIStateResponse,
    AnalyzeIntentRequest,
    AnalyzeIntentResponse,
    ConversationInsightsResponse,
    HandoffRequest,
    HandoffResponse,
    SuggestReplyResponse,
    ToggleAIRequest,
    ToggleAutoReplyRequest,
)
from app.ai_live.services.handoff_service import HandoffService
from app.ai_live.services.insights_service import AIInsightsService
from app.ai_live.services.suggestions_service import AISuggestionsService
from app.core.security.dependencies import TenantContext
from app.core.security.permissions import require_permission

router = APIRouter()


@router.get("/conversations/{conversation_id}/state", response_model=AIStateResponse)
async def get_ai_state(
    conversation_id: UUID,
    tenant: Annotated[TenantContext, Depends(require_permission("conversations:read"))],
    repository: Annotated[ConversationAIRepository, Depends(get_ai_live_repository)],
) -> AIStateResponse:
    state = await repository.get_or_create_state(
        empresa_id=tenant.empresa_id, conversation_id=conversation_id
    )
    return AIStateResponse.model_validate(state)


@router.post("/conversations/{conversation_id}/suggest-reply", response_model=SuggestReplyResponse)
async def suggest_reply(
    conversation_id: UUID,
    tenant: Annotated[TenantContext, Depends(require_permission("ai:respond"))],
    suggestions_service: Annotated[AISuggestionsService, Depends(get_ai_suggestions_service)],
) -> SuggestReplyResponse:
    suggestions = await suggestions_service.suggest_replies(
        empresa_id=tenant.empresa_id,
        conversation_id=conversation_id,
    )
    return SuggestReplyResponse(suggestions=suggestions)


@router.get("/conversations/{conversation_id}/insights", response_model=ConversationInsightsResponse)
async def get_insights(
    conversation_id: UUID,
    tenant: Annotated[TenantContext, Depends(require_permission("sales:read"))],
    insights_service: Annotated[AIInsightsService, Depends(get_ai_insights_service)],
) -> ConversationInsightsResponse:
    return await insights_service.get_conversation_insights(
        empresa_id=tenant.empresa_id,
        conversation_id=conversation_id,
    )


@router.patch("/conversations/{conversation_id}/toggle-ai", response_model=AIStateResponse)
async def toggle_ai(
    conversation_id: UUID,
    payload: ToggleAIRequest,
    tenant: Annotated[TenantContext, Depends(require_permission("conversations:write"))],
    repository: Annotated[ConversationAIRepository, Depends(get_ai_live_repository)],
) -> AIStateResponse:
    state = await repository.toggle_ai(
        empresa_id=tenant.empresa_id,
        conversation_id=conversation_id,
        enabled=payload.ai_enabled,
    )
    return AIStateResponse.model_validate(state)


@router.patch("/conversations/{conversation_id}/toggle-auto-reply", response_model=AIStateResponse)
async def toggle_auto_reply(
    conversation_id: UUID,
    payload: ToggleAutoReplyRequest,
    tenant: Annotated[TenantContext, Depends(require_permission("conversations:write"))],
    repository: Annotated[ConversationAIRepository, Depends(get_ai_live_repository)],
) -> AIStateResponse:
    state = await repository.toggle_auto_reply(
        empresa_id=tenant.empresa_id,
        conversation_id=conversation_id,
        enabled=payload.auto_reply_enabled,
    )
    return AIStateResponse.model_validate(state)


@router.get("/conversations/{conversation_id}/events", response_model=AIEventListResponse)
async def list_ai_events(
    conversation_id: UUID,
    tenant: Annotated[TenantContext, Depends(require_permission("conversations:read"))],
    repository: Annotated[ConversationAIRepository, Depends(get_ai_live_repository)],
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> AIEventListResponse:
    events, total = await repository.list_events(
        empresa_id=tenant.empresa_id,
        conversation_id=conversation_id,
        limit=limit,
        offset=offset,
    )
    return AIEventListResponse(
        events=[e for e in events],
        total=total,
    )


@router.post("/conversations/{conversation_id}/handoff", response_model=HandoffResponse)
async def request_handoff(
    conversation_id: UUID,
    payload: HandoffRequest,
    tenant: Annotated[TenantContext, Depends(require_permission("conversations:write"))],
    repository: Annotated[ConversationAIRepository, Depends(get_ai_live_repository)],
    handoff_service: Annotated[HandoffService, Depends(get_handoff_service)],
) -> HandoffResponse:
    state = await repository.get_or_create_state(
        empresa_id=tenant.empresa_id, conversation_id=conversation_id
    )
    state.escalation_required = True
    await repository.update_state(state=state, escalation_required=True)
    await repository.add_event(
        empresa_id=tenant.empresa_id,
        conversation_id=conversation_id,
        event_type="handoff_requested",
        payload={"reason": payload.reason or "Agent requested handoff"},
    )
    return HandoffResponse(success=True, message="Handoff requested successfully")


@router.post("/conversations/{conversation_id}/analyze-intent", response_model=AnalyzeIntentResponse)
async def analyze_intent(
    conversation_id: UUID,
    payload: AnalyzeIntentRequest,
    tenant: Annotated[TenantContext, Depends(require_permission("sales:read"))],
    repository: Annotated[ConversationAIRepository, Depends(get_ai_live_repository)],
) -> AnalyzeIntentResponse:
    from app.ai.classifiers.intent_classifier import IntentClassifierService

    classifier = IntentClassifierService()
    classification = await classifier.classify(payload.message)

    state = await repository.get_or_create_state(
        empresa_id=tenant.empresa_id, conversation_id=conversation_id
    )
    await repository.update_state(
        state=state,
        last_detected_intent=classification.intent.value,
    )

    sentiment = "neutral"
    urgency_score = 0.5
    lead_temperature = "warm"
    if classification.confidence >= 0.8:
        sentiment = "positive" if classification.intent.value in ("purchase_intent", "greeting") else "negative"
        urgency_score = 0.8 if classification.intent.value in ("complaint", "pricing_intent") else 0.5
        lead_temperature = "hot" if classification.intent.value == "purchase_intent" else "warm"

    await repository.add_event(
        empresa_id=tenant.empresa_id,
        conversation_id=conversation_id,
        event_type="intent_analyzed",
        payload={"intent": classification.intent.value},
    )

    return AnalyzeIntentResponse(
        detected_intent=classification.intent.value,
        sentiment=sentiment,
        urgency_score=urgency_score,
        lead_temperature=lead_temperature,
        confidence=classification.confidence,
    )
