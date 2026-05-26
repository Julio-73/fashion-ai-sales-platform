from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from app.sales.intents.intent import IntentType

# ── Insights ─────────────────────────────────────────────────

class IntentCount(BaseModel):
    intent: str
    count: int


class TopCustomer(BaseModel):
    customer_id: str
    full_name: str
    lead_score: int
    priority: str
    lead_status: str
    last_interaction_at: datetime | None = None


class SalesInsightsResponse(BaseModel):
    total_hot_leads: int
    total_interested: int
    total_negotiation: int
    total_converted: int
    top_customers: list[TopCustomer]
    high_priority_customers: list[TopCustomer]
    most_detected_intents: list[IntentCount]
    recent_sales_activity: int


# ── Customer Sales Profile ───────────────────────────────────

class ConversationMetrics(BaseModel):
    total_conversations: int
    total_messages: int
    last_message_at: datetime | None = None
    last_message_content: str | None = None


class CustomerSalesProfileResponse(BaseModel):
    customer_id: str
    full_name: str
    email: str | None = None
    phone: str | None = None
    lead_score: int
    lead_status: str
    priority: str
    tags: list[str]
    detected_intents: list[str]
    activity_level: str
    last_interaction_at: datetime | None = None
    conversation_metrics: ConversationMetrics
    sales_summary: str


# ── Analyze Message ──────────────────────────────────────────

class AnalyzeMessageRequest(BaseModel):
    customer_id: str
    message: str


class AnalyzeMessageResponse(BaseModel):
    detected_intent: IntentType
    score_impact: int
    recommended_action: str
    lead_status_prediction: str


# ── Recommendations ──────────────────────────────────────────

class CustomerRecommendation(BaseModel):
    customer_id: str
    full_name: str
    lead_score: int
    priority: str
    lead_status: str
    reason: str
    days_since_last_interaction: int | None = None


class SalesRecommendationsResponse(BaseModel):
    customers_to_follow_up: list[CustomerRecommendation]
    hot_leads: list[CustomerRecommendation]
    negotiation_leads: list[CustomerRecommendation]
    inactive_customers: list[CustomerRecommendation]
    upsell_opportunities: list[CustomerRecommendation]


# ── Top Leads ────────────────────────────────────────────────

class TopLead(BaseModel):
    customer_id: str
    full_name: str
    lead_score: int
    priority: str
    lead_status: str
    conversation_count: int
    last_interaction_at: datetime | None = None
    conversion_probability: str


class TopLeadsResponse(BaseModel):
    leads: list[TopLead]
    total: int


# ── Activity Timeline ────────────────────────────────────────

class ActivityEvent(BaseModel):
    event_type: Literal["message", "lead_status_change", "conversation", "customer_activity"]
    description: str
    timestamp: datetime
    customer_id: str | None = None
    customer_name: str | None = None
    metadata: dict | None = None


class SalesActivityResponse(BaseModel):
    events: list[ActivityEvent]
    total: int
