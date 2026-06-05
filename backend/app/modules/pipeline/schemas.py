"""Pydantic IO contracts for the pipeline module."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.modules.pipeline.models import (
    CLOSED_STAGES,
    OPEN_STAGES,
    PIPELINE_STAGE_VALUES,
    WON_STAGE,
)


StageName = Literal[
    "new_lead", "contacted", "qualified", "proposal", "negotiation", "won", "lost"
]


class PipelineStageInfo(BaseModel):
    """Static metadata about a stage — labels, ordering, terminal flag."""

    key: str
    label: str
    description: str
    is_open: bool
    is_terminal: bool
    order: int
    default_probability: int
    color: str


class CustomerSummary(BaseModel):
    """Compact customer projection embedded in pipeline responses."""

    id: UUID
    full_name: str
    email: str | None = None
    phone: str | None = None
    whatsapp: str | None = None
    lead_status: str | None = None
    priority: str | None = None
    lead_score: int = 0
    is_vip: bool = False
    last_interaction_at: datetime | None = None
    conversation_count: int = 0
    lifetime_value: Decimal = Decimal("0")
    orders_count: int = 0


def _clamp_0_100(v: object) -> int:
    """Clamp an incoming value to the closed interval ``[0, 100]``.

    Non-numeric values fall through to the standard ``Field(ge=0, le=100)``
    check so the validator raises a meaningful ``ValidationError`` instead
    of silently coercing.
    """
    if isinstance(v, bool):
        # bool is a subclass of int — be explicit to avoid surprises.
        return 100 if v else 0
    if isinstance(v, (int, float)):
        return max(0, min(100, int(v)))
    return v  # type: ignore[return-value]


class AIScoreBreakdown(BaseModel):
    """Decomposition of a commercial AI score.

    Each factor is a 0-100 sub-score. ``total`` is the weighted sum.

    Out-of-range integers are **clamped** to ``[0, 100]`` (not rejected)
    so that defensive construction (e.g. ``model_construct``) cannot leak
    un-bounded values into API responses.
    """

    model_config = ConfigDict()

    total: int = Field(ge=0, le=100)
    intent: int = Field(ge=0, le=100, default=0)
    engagement: int = Field(ge=0, le=100, default=0)
    recency: int = Field(ge=0, le=100, default=0)
    monetary: int = Field(ge=0, le=100, default=0)
    sentiment: int = Field(ge=0, le=100, default=50)
    rationale: list[str] = Field(default_factory=list)

    @field_validator(
        "total", "intent", "engagement", "recency", "monetary", "sentiment",
        mode="before",
    )
    @classmethod
    def _clamp_to_0_100(cls, v: object) -> object:
        return _clamp_0_100(v)


class PipelineItemBase(BaseModel):
    title: Annotated[str, Field(min_length=1, max_length=200)]
    estimated_value: Decimal = Field(default=Decimal("0"), ge=0)
    probability: Annotated[int, Field(ge=0, le=100)] = 0
    stage: StageName = "new_lead"
    notes: str | None = None
    channel: str | None = Field(default=None, max_length=32)
    is_vip: bool = False

    @field_validator("stage")
    @classmethod
    def _stage_in_enum(cls, v: str) -> str:
        if v not in PIPELINE_STAGE_VALUES:
            raise ValueError(f"unknown stage '{v}'")
        return v


class PipelineItemCreate(PipelineItemBase):
    customer_id: UUID | None = None
    conversation_id: UUID | None = None
    order_id: UUID | None = None


class PipelineItemUpdate(BaseModel):
    """All fields optional. Stage moves go through ``/move-stage``."""

    title: str | None = Field(default=None, min_length=1, max_length=200)
    estimated_value: Decimal | None = Field(default=None, ge=0)
    probability: int | None = Field(default=None, ge=0, le=100)
    notes: str | None = None
    channel: str | None = Field(default=None, max_length=32)
    is_vip: bool | None = None
    customer_id: UUID | None = None
    conversation_id: UUID | None = None
    order_id: UUID | None = None


class PipelineItemMoveStage(BaseModel):
    target_stage: StageName
    probability: int | None = Field(default=None, ge=0, le=100)
    notes: str | None = None
    won_reason: str | None = Field(default=None, max_length=120)
    lost_reason: str | None = Field(default=None, max_length=120)

    @field_validator("target_stage")
    @classmethod
    def _stage_in_enum(cls, v: str) -> str:
        if v not in PIPELINE_STAGE_VALUES:
            raise ValueError(f"unknown stage '{v}'")
        return v


class PipelineItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    empresa_id: UUID
    customer_id: UUID | None
    conversation_id: UUID | None
    order_id: UUID | None
    title: str
    estimated_value: Decimal
    probability: int
    stage: str
    stage_entered_at: datetime
    last_activity_at: datetime
    notes: str | None
    won_reason: str | None
    lost_reason: str | None
    position: int
    channel: str | None
    is_vip: bool
    created_at: datetime
    updated_at: datetime

    customer: CustomerSummary | None = None
    ai_score: AIScoreBreakdown | None = None


class PipelineBoardResponse(BaseModel):
    """Response payload for ``GET /pipeline/board``."""

    items: list[PipelineItemResponse]
    total: int
    by_stage: dict[str, int]
    value_by_stage: dict[str, float]


class PipelineMetricsResponse(BaseModel):
    """Response payload for ``GET /pipeline/metrics``."""

    total_open: int
    total_closed_won: int
    total_closed_lost: int
    new_leads: int = 0
    open_value: float
    weighted_open_value: float
    won_value: float
    lost_value: float
    conversion_rate_pct: float
    average_deal_value: float
    average_time_to_close_days: float
    average_time_in_current_stage_days: float
    oldest_unstuck_days: int
    alerts_count: int
    by_stage: dict[str, dict[str, float]]
    by_channel: dict[str, dict[str, float]]
    by_priority: dict[str, dict[str, float]]


class PipelineFunnelResponse(BaseModel):
    """Funnel data for the visual reporting page."""

    stages: list[dict[str, float | str | int]]
    total_open: int
    total_closed: int
    won_value: float
    lost_value: float


class PipelineAlert(BaseModel):
    """A single automation alert returned by the engine."""

    id: str
    deal_id: UUID
    deal_title: str
    customer_id: UUID | None
    rule: str
    severity: Literal["info", "warning", "critical"]
    message: str
    suggested_action: str
    stage: str
    days_in_stage: int
    created_at: datetime


class PipelineAlertsResponse(BaseModel):
    alerts: list[PipelineAlert]
    total: int


class PipelineRecommendation(BaseModel):
    """AI-style recommendation attached to a deal."""

    deal_id: UUID
    score: int = Field(ge=0, le=100)
    breakdown: AIScoreBreakdown
    next_best_action: str
    suggested_channel: str | None
    suggested_stage: str | None
    notes: list[str]


class PipelineRecommendationsResponse(BaseModel):
    recommendations: list[PipelineRecommendation]
    total: int


class PipelineAIScoreRequest(BaseModel):
    deal_id: UUID


class PipelineAIScoreResponse(BaseModel):
    deal_id: UUID
    score: int = Field(ge=0, le=100)
    breakdown: AIScoreBreakdown


class PipelineDashboardResponse(BaseModel):
    """Aggregate reporting payload used by the dashboard page."""

    metrics: PipelineMetricsResponse
    funnel: PipelineFunnelResponse
    alerts: PipelineAlertsResponse
    top_deals: list[PipelineItemResponse]
    generated_at: datetime


__all__ = [
    "StageName",
    "PipelineStageInfo",
    "CustomerSummary",
    "AIScoreBreakdown",
    "PipelineItemBase",
    "PipelineItemCreate",
    "PipelineItemUpdate",
    "PipelineItemMoveStage",
    "PipelineItemResponse",
    "PipelineBoardResponse",
    "PipelineMetricsResponse",
    "PipelineFunnelResponse",
    "PipelineAlert",
    "PipelineAlertsResponse",
    "PipelineRecommendation",
    "PipelineRecommendationsResponse",
    "PipelineAIScoreRequest",
    "PipelineAIScoreResponse",
    "PipelineDashboardResponse",
    "OPEN_STAGES",
    "CLOSED_STAGES",
    "WON_STAGE",
]
