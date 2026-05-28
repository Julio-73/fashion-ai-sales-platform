from datetime import datetime
from decimal import Decimal
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


class RichCustomerProfile(BaseModel):
    customer_id: UUID
    full_name: str
    email: str | None = None
    phone: str | None = None
    tags: list[str] = Field(default_factory=list)
    lead_score: float = 0.0
    lead_status: str = "new"
    priority: str = "cold"
    total_conversations: int = 0
    last_interaction_at: datetime | None = None
    favorite_categories: list[str] = Field(default_factory=list)
    preferred_colors: list[str] = Field(default_factory=list)
    preferred_sizes: list[str] = Field(default_factory=list)
    average_order_value: float = 0.0
    customer_lifetime_value: float = 0.0
    is_vip: bool = False
    detected_preferences: dict[str, str] = Field(default_factory=dict)


class MessageHistoryItem(BaseModel):
    role: str = ""
    content: str = ""
    created_at: datetime | None = None
    intent: str | None = None
    sentiment: str | None = None


class ConversationHistory(BaseModel):
    conversation_id: UUID | None = None
    messages: list[MessageHistoryItem] = Field(default_factory=list)
    detected_intents: list[str] = Field(default_factory=list)
    sentiment_history: list[str] = Field(default_factory=list)
    has_escalations: bool = False
    has_handoffs: bool = False
    average_response_time_minutes: float = 0.0
    total_messages: int = 0
    status: str = "active"


class ProductInterest(BaseModel):
    product_id: UUID | None = None
    product_name: str = ""
    category: str = ""
    viewed_count: int = 0
    asked_count: int = 0
    stock_available: int = 0
    has_stock: bool = False
    price: float = 0.0


class ProductContextDetail(BaseModel):
    products_viewed: list[ProductInterest] = Field(default_factory=list)
    products_asked: list[ProductInterest] = Field(default_factory=list)
    frequent_categories: list[str] = Field(default_factory=list)
    preferred_styles: list[str] = Field(default_factory=list)
    upsell_candidates: list[ProductInterest] = Field(default_factory=list)
    total_products_queried: int = 0


class SalesContextDetail(BaseModel):
    conversion_probability: str = "low"
    negotiation_stage: str = "initial"
    discount_sensitivity: str = "unknown"
    buying_intent_trend: str = "stable"
    lead_score_evolution: list[dict] = Field(default_factory=list)
    churn_risk: str = "low"
    is_hot_lead: bool = False
    is_premium_customer: bool = False


class RichContextData(BaseModel):
    customer: RichCustomerProfile
    conversation: ConversationHistory = Field(default_factory=ConversationHistory)
    products: ProductContextDetail = Field(default_factory=ProductContextDetail)
    sales: SalesContextDetail = Field(default_factory=SalesContextDetail)


class RichContextResponse(BaseModel):
    context: RichContextData


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
    rich_context: RichContextData | None = None
