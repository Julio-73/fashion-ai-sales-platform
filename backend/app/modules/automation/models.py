"""ORM models for the Automation Engine Enterprise V1.

Three new tables — all additive, no FK writes against any frozen
module's tables. We only read from them.

* ``automation_rules``   — declarative rule catalog (seeded with the 7
                            initial rules from spec).
* ``automation_tasks``   — actionable items surfaced in
                            ``/dashboard/tasks``.
* ``automation_events``  — immutable audit log of every rule
                            execution; powers the alert center and
                            metrics.
"""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TenantMixin, TimestampMixin, UUIDPrimaryKeyMixin


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

TASK_STATUS_VALUES: tuple[str, ...] = (
    "pending",
    "in_progress",
    "completed",
    "cancelled",
    "overdue",
)
"""Lifecycle of an automation task."""

TASK_PRIORITY_VALUES: tuple[str, ...] = ("low", "medium", "high", "critical")
"""Priority bucket used by the UI."""

TASK_TYPE_VALUES: tuple[str, ...] = (
    "follow_up",
    "call",
    "proposal",
    "meeting",
    "recovery",
    "alert",
    "win_log",
    "loss_log",
    "pipeline_event",
    "inventory_check",
    "order_risk",
)
"""Discriminator for the task type — drives icons and filters in the UI."""

ENTITY_TYPE_VALUES: tuple[str, ...] = (
    "customer",
    "pipeline_item",
    "conversation",
    "order",
    "inventory_item",
    "none",
)
"""Polymorphic reference stored in ``entity_type``."""

EVENT_SEVERITY_VALUES: tuple[str, ...] = ("info", "warning", "critical")


# ---------------------------------------------------------------------------
# Rule keys — referenced by the engine and the seed
# ---------------------------------------------------------------------------
RULE_001 = "LEAD_NO_RESPONSE_24H"
RULE_002 = "LEAD_NO_RESPONSE_48H"
RULE_003 = "NEGOTIATION_STUCK_7D"
RULE_004 = "VIP_CUSTOMER_INACTIVE_30D"
RULE_005 = "NEW_HIGH_VALUE_LEAD"
RULE_006 = "PIPELINE_WON"
RULE_007 = "PIPELINE_LOST"


DEFAULT_RULES: tuple[dict, ...] = (
    dict(
        rule_key=RULE_001,
        name="Lead sin respuesta 24h",
        description=(
            "Crea una tarea de seguimiento cuando un lead capturado no "
            "interactúa en 24 horas."
        ),
        trigger_type="customer_idle",
        default_priority="medium",
        default_severity="warning",
        task_type="follow_up",
    ),
    dict(
        rule_key=RULE_002,
        name="Lead sin respuesta 48h",
        description=(
            "Crea una alerta crítica y tarea cuando un lead sigue "
            "silencioso tras 48 horas."
        ),
        trigger_type="customer_idle",
        default_priority="high",
        default_severity="critical",
        task_type="alert",
    ),
    dict(
        rule_key=RULE_003,
        name="Negociación estancada 7d",
        description=(
            "Crea una tarea de seguimiento para deals en 'negotiation' "
            "más de 7 días."
        ),
        trigger_type="pipeline_stage",
        default_priority="high",
        default_severity="warning",
        task_type="follow_up",
    ),
    dict(
        rule_key=RULE_004,
        name="Cliente VIP inactivo 30d",
        description=(
            "Crea una tarea de recuperación para clientes VIP sin "
            "interacción en 30 días."
        ),
        trigger_type="customer_idle",
        default_priority="critical",
        default_severity="critical",
        task_type="recovery",
    ),
    dict(
        rule_key=RULE_005,
        name="Nuevo lead de alto valor",
        description=(
            "Crea una alerta IA cuando entra un nuevo lead con valor "
            "estimado alto o LTV relevante."
        ),
        trigger_type="pipeline_new",
        default_priority="high",
        default_severity="info",
        task_type="alert",
    ),
    dict(
        rule_key=RULE_006,
        name="Pipeline ganado",
        description=(
            "Registra un evento cuando un deal se mueve a 'won' — "
            "alimenta analytics y reporting."
        ),
        trigger_type="pipeline_won",
        default_priority="low",
        default_severity="info",
        task_type="win_log",
    ),
    dict(
        rule_key=RULE_007,
        name="Pipeline perdido",
        description=(
            "Registra un evento y tarea cuando un deal se mueve a "
            "'lost' — guarda el motivo."
        ),
        trigger_type="pipeline_lost",
        default_priority="medium",
        default_severity="warning",
        task_type="loss_log",
    ),
)


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class AutomationRule(UUIDPrimaryKeyMixin, TenantMixin, TimestampMixin, Base):
    """Declarative rule catalog. Seeded with the 7 default rules."""

    __tablename__ = "automation_rules"
    __table_args__ = (
        UniqueConstraint("empresa_id", "rule_key", name="uq_automation_rules__empresa_id_rule_key"),
        Index("idx_automation_rules__empresa_id_enabled", "empresa_id", "enabled"),
        CheckConstraint(
            "trigger_type IN ("
            "'customer_idle','pipeline_stage','pipeline_new',"
            "'pipeline_won','pipeline_lost','order_risk',"
            "'inventory_low')",
            name="ck_automation_rules__trigger_type",
        ),
    )

    rule_key: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    trigger_type: Mapped[str] = mapped_column(String(32), nullable=False)
    enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
    config: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=dict, server_default="{}"
    )


class AutomationTask(UUIDPrimaryKeyMixin, TenantMixin, TimestampMixin, Base):
    """Actionable item surfaced in /dashboard/tasks."""

    __tablename__ = "automation_tasks"
    __table_args__ = (
        Index("idx_automation_tasks__empresa_id_status_due", "empresa_id", "status", "due_date"),
        Index("idx_automation_tasks__empresa_id_priority", "empresa_id", "priority"),
        Index("idx_automation_tasks__empresa_id_rule_id", "empresa_id", "rule_id"),
        Index("idx_automation_tasks__empresa_id_customer", "empresa_id", "customer_id"),
        Index("idx_automation_tasks__empresa_id_pipeline_item", "empresa_id", "pipeline_item_id"),
        Index("idx_automation_tasks__empresa_id_due_date", "empresa_id", "due_date"),
        CheckConstraint(
            "status IN ('pending','in_progress','completed','cancelled','overdue')",
            name="ck_automation_tasks__status",
        ),
        CheckConstraint(
            "priority IN ('low','medium','high','critical')",
            name="ck_automation_tasks__priority",
        ),
        CheckConstraint(
            "task_type IN ("
            "'follow_up','call','proposal','meeting','recovery',"
            "'alert','win_log','loss_log','pipeline_event',"
            "'inventory_check','order_risk')",
            name="ck_automation_tasks__task_type",
        ),
    )

    rule_id: Mapped[UUID | None] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("automation_rules.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Optional polymorphic reference — never enforced at the FK level
    # for entities that may be deleted (we keep the audit row).
    customer_id: Mapped[UUID | None] = mapped_column(
        PostgresUUID(as_uuid=True), nullable=True
    )
    pipeline_item_id: Mapped[UUID | None] = mapped_column(
        PostgresUUID(as_uuid=True), nullable=True
    )
    conversation_id: Mapped[UUID | None] = mapped_column(
        PostgresUUID(as_uuid=True), nullable=True
    )

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    task_type: Mapped[str] = mapped_column(String(32), nullable=False, default="follow_up")
    priority: Mapped[str] = mapped_column(String(16), nullable=False, default="medium")
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending")

    ai_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_next_action: Mapped[str | None] = mapped_column(String(200), nullable=True)
    ai_score: Mapped[int | None] = mapped_column(Integer, nullable=True)

    due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class AutomationEvent(UUIDPrimaryKeyMixin, TenantMixin, Base):
    """Immutable audit log. ``created_at`` is set by the DB; we never
    update these rows."""

    __tablename__ = "automation_events"
    __table_args__ = (
        Index("idx_automation_events__empresa_id_created_at", "empresa_id", "created_at"),
        Index("idx_automation_events__empresa_id_rule_key", "empresa_id", "rule_key"),
        Index("idx_automation_events__empresa_id_entity", "empresa_id", "entity_type", "entity_id"),
        CheckConstraint(
            "severity IN ('info','warning','critical')",
            name="ck_automation_events__severity",
        ),
        CheckConstraint(
            "entity_type IN ("
            "'customer','pipeline_item','conversation','order',"
            "'inventory_item','none')",
            name="ck_automation_events__entity_type",
        ),
    )

    rule_id: Mapped[UUID | None] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("automation_rules.id", ondelete="SET NULL"),
        nullable=True,
    )
    rule_key: Mapped[str] = mapped_column(String(64), nullable=False)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(32), nullable=False, default="none")
    entity_id: Mapped[UUID | None] = mapped_column(PostgresUUID(as_uuid=True), nullable=True)
    severity: Mapped[str] = mapped_column(String(16), nullable=False, default="info")
    payload: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=dict, server_default="{}"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
        server_default=func.now(),
        nullable=False,
    )


__all__ = [
    "AutomationRule",
    "AutomationTask",
    "AutomationEvent",
    "TASK_STATUS_VALUES",
    "TASK_PRIORITY_VALUES",
    "TASK_TYPE_VALUES",
    "ENTITY_TYPE_VALUES",
    "EVENT_SEVERITY_VALUES",
    "RULE_001",
    "RULE_002",
    "RULE_003",
    "RULE_004",
    "RULE_005",
    "RULE_006",
    "RULE_007",
    "DEFAULT_RULES",
]
