from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID

from app.sales.intents.intent import IntentType


@dataclass
class SalesIntelligenceInput:
    empresa_id: UUID
    customer_id: UUID
    conversation_id: UUID
    message_content: str
    message_sender: str
    conversation_status: str
    message_count: int
    conversation_count: int
    current_lead_status: str
    last_interaction_at: object | None


@dataclass
class SalesIntelligenceResult:
    primary_intent: IntentType = IntentType.unknown
    all_intents: list[tuple[IntentType, int]] = field(default_factory=list)
    lead_score: int = 0
    lead_priority: str = "cold"
    suggested_lead_status: str | None = None
    suggested_tags: list[str] = field(default_factory=list)
    reason: str | None = None
