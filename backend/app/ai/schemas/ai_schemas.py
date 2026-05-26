from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


class IntentType(str, Enum):
    pricing = "pricing"
    purchase_intent = "purchase_intent"
    negotiation = "negotiation"
    delivery = "delivery"
    greeting = "greeting"
    support = "support"
    return_request = "return_request"
    product_question = "product_question"
    sizing = "sizing"
    unknown = "unknown"


class ConversationStage(str, Enum):
    new = "new"
    active = "active"
    negotiation = "negotiation"
    closing = "closing"
    converted = "converted"
    lost = "lost"


class SalesAction(str, Enum):
    follow_up = "follow_up"
    escalate = "escalate"
    suggest_discount = "suggest_discount"
    suggest_upsell = "suggest_upsell"
    suggest_cross_sell = "suggest_cross_sell"
    no_action = "no_action"


class ReplyType(str, Enum):
    sales = "sales"
    support = "support"
    greeting = "greeting"
    follow_up = "follow_up"
    escalation = "escalation"
    no_reply = "no_reply"


class ClassifyRequest(BaseModel):
    message: str = Field(min_length=1, max_length=5000)
    empresa_id: UUID


class IntentClassification(BaseModel):
    intent: IntentType
    confidence: float = Field(ge=0.0, le=1.0)
    matched_keywords: list[str] = Field(default_factory=list)


class ClassifyResponse(BaseModel):
    classification: IntentClassification


class ContextRequest(BaseModel):
    empresa_id: UUID
    customer_id: UUID
    conversation_id: UUID


class CustomerProfileRef(BaseModel):
    customer_id: UUID | None = None
    customer_name: str = ""
    lead_score: float = 0.0
    tags: list[str] = Field(default_factory=list)


class ContextData(BaseModel):
    customer: CustomerProfileRef
    recent_messages: list[str] = Field(default_factory=list)
    conversation_stage: ConversationStage = ConversationStage.new
    product_interests: list[str] = Field(default_factory=list)


class ContextResponse(BaseModel):
    context: ContextData


class OrchestratorRequest(BaseModel):
    message: str = Field(min_length=1, max_length=5000)
    empresa_id: UUID
    customer_id: UUID
    conversation_id: UUID


class OrchestratorResponse(BaseModel):
    intent: IntentType
    intent_confidence: float = Field(ge=0.0, le=1.0)
    sales_action: SalesAction
    should_reply: bool = True
    reply_type: ReplyType
    generated_response: str = ""
    recommended_product_ids: list[UUID] = Field(default_factory=list)
    suggested_discount_pct: float | None = None
    escalate_reason: str | None = None
