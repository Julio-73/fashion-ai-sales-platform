from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class AIStateResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    empresa_id: UUID
    conversation_id: UUID
    ai_enabled: bool
    auto_reply_enabled: bool
    escalation_required: bool
    last_detected_intent: str | None = None
    sentiment: str | None = None
    urgency_score: float | None = None
    lead_temperature: str | None = None
    ai_last_response: str | None = None
    ai_confidence: float | None = None
    created_at: datetime
    updated_at: datetime


class SuggestedReply(BaseModel):
    text: str
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str


class SuggestReplyResponse(BaseModel):
    suggestions: list[SuggestedReply]


class ConversationInsightsResponse(BaseModel):
    detected_intent: str
    urgency: str
    lead_score: float
    probability_to_buy: float
    recommended_action: str
    escalation_recommended: bool
    customer_activity_level: str
    last_interaction: str | None = None
    suggested_next_step: str


class AIEventResponse(BaseModel):
    id: UUID
    empresa_id: UUID
    conversation_id: UUID
    event_type: str
    payload: str | None = None
    created_at: datetime


class AIEventListResponse(BaseModel):
    events: list[AIEventResponse]
    total: int


class ToggleAIRequest(BaseModel):
    ai_enabled: bool


class ToggleAutoReplyRequest(BaseModel):
    auto_reply_enabled: bool


class AnalyzeIntentRequest(BaseModel):
    message: str = Field(..., min_length=1)


class AnalyzeIntentResponse(BaseModel):
    detected_intent: str
    sentiment: str
    urgency_score: float
    lead_temperature: str
    confidence: float


class HandoffRequest(BaseModel):
    reason: str | None = None


class HandoffResponse(BaseModel):
    success: bool
    message: str
