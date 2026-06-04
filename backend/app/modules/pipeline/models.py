"""ORM models for the pipeline module.

Only the new table ``sales_pipeline_items``. It references (read-only)
``clientes``, ``conversations_core`` and ``orders``. No migrations
back-walk: deleting a referenced customer/conversation/order sets the
FK to NULL on the pipeline row (``ON DELETE SET NULL``) so the deal
history is preserved.
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TenantMixin, TimestampMixin, UUIDPrimaryKeyMixin


PIPELINE_STAGE_VALUES: tuple[str, ...] = (
    "new_lead",
    "contacted",
    "qualified",
    "proposal",
    "negotiation",
    "won",
    "lost",
)
"""Allowed stages for a deal. Keep in sync with the CHECK constraint
``ck_sales_pipeline_items__stage`` created in
``alembic/versions/0015_sales_pipeline.py``."""


OPEN_STAGES: frozenset[str] = frozenset(
    {"new_lead", "contacted", "qualified", "proposal", "negotiation"}
)
"""Stages where the deal is still considered open."""

CLOSED_STAGES: frozenset[str] = frozenset({"won", "lost"})
"""Terminal stages."""


WON_STAGE = "won"
LOST_STAGE = "lost"
NEW_LEAD_STAGE = "new_lead"


def is_valid_stage(stage: str) -> bool:
    """Return ``True`` if ``stage`` is a known pipeline stage."""
    return stage in PIPELINE_STAGE_VALUES


class SalesPipelineItem(UUIDPrimaryKeyMixin, TenantMixin, TimestampMixin, Base):
    """A materialised sales deal in a given stage of the funnel."""

    __tablename__ = "sales_pipeline_items"
    __table_args__ = (
        CheckConstraint(
            "stage in ('new_lead', 'contacted', 'qualified', 'proposal', 'negotiation', 'won', 'lost')",
            name="ck_sales_pipeline_items__stage",
        ),
        CheckConstraint(
            "probability between 0 and 100",
            name="ck_sales_pipeline_items__probability",
        ),
        CheckConstraint(
            "estimated_value >= 0",
            name="ck_sales_pipeline_items__estimated_value",
        ),
        Index(
            "idx_sales_pipeline_items__empresa_stage_last",
            "empresa_id",
            "stage",
            "last_activity_at",
        ),
        Index(
            "idx_sales_pipeline_items__empresa_stage_entered",
            "empresa_id",
            "stage_entered_at",
        ),
        Index(
            "idx_sales_pipeline_items__empresa_customer",
            "empresa_id",
            "customer_id",
        ),
    )

    customer_id: Mapped[UUID | None] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("clientes.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    conversation_id: Mapped[UUID | None] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("conversations_core.id", ondelete="SET NULL"),
        nullable=True,
    )
    order_id: Mapped[UUID | None] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="SET NULL"),
        nullable=True,
    )

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    estimated_value: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0")
    )
    probability: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    stage: Mapped[str] = mapped_column(
        String(32), nullable=False, default=NEW_LEAD_STAGE
    )

    stage_entered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    last_activity_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    won_reason: Mapped[str | None] = mapped_column(String(120), nullable=True)
    lost_reason: Mapped[str | None] = mapped_column(String(120), nullable=True)

    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    channel: Mapped[str | None] = mapped_column(String(32), nullable=True)
    is_vip: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )


__all__ = [
    "SalesPipelineItem",
    "PIPELINE_STAGE_VALUES",
    "OPEN_STAGES",
    "CLOSED_STAGES",
    "WON_STAGE",
    "LOST_STAGE",
    "NEW_LEAD_STAGE",
    "is_valid_stage",
]
