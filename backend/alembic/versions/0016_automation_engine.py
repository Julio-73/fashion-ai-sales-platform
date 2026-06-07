"""add automation engine tables

Revision ID: 0016_automation_engine
Revises: 0015_sales_pipeline
Create Date: 2026-06-07

AUTOMATION ENGINE ENTERPRISE V1 — three new tables, all additive:

* ``automation_rules``   — declarative rule catalog (seeded with the 7
                           initial rules from spec).
* ``automation_tasks``   — actionable items surfaced in
                           ``/dashboard/tasks``.
* ``automation_events``  — immutable audit log of every rule
                           execution; powers the alert center and
                           metrics.

No FK writes are performed on any frozen module's tables. We only
read from ``clientes``, ``conversations_core``, ``messages_core``,
``orders``, ``inventory_items``, ``sales_pipeline_items`` and
``whatsapp_messages``.
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "0016_automation_engine"
down_revision: str | None = "0015_sales_pipeline"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # -------------------------------------------------------------------------
    # automation_rules
    # -------------------------------------------------------------------------
    op.create_table(
        "automation_rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("empresa_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("empresas.id", ondelete="RESTRICT"), nullable=False, index=True),
        sa.Column("rule_key", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("trigger_type", sa.String(length=32), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("config", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("empresa_id", "rule_key", name="uq_automation_rules__empresa_id_rule_key"),
        sa.CheckConstraint(
            "trigger_type IN ("
            "'customer_idle','pipeline_stage','pipeline_new',"
            "'pipeline_won','pipeline_lost','order_risk',"
            "'inventory_low')",
            name="ck_automation_rules__trigger_type",
        ),
    )
    op.create_index(
        "idx_automation_rules__empresa_id_enabled",
        "automation_rules",
        ["empresa_id", "enabled"],
    )

    # -------------------------------------------------------------------------
    # automation_tasks
    # -------------------------------------------------------------------------
    op.create_table(
        "automation_tasks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("empresa_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("empresas.id", ondelete="RESTRICT"), nullable=False, index=True),
        sa.Column(
            "rule_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("automation_rules.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("customer_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("pipeline_item_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("task_type", sa.String(length=32), nullable=False, server_default=sa.text("'follow_up'")),
        sa.Column("priority", sa.String(length=16), nullable=False, server_default=sa.text("'medium'")),
        sa.Column("status", sa.String(length=16), nullable=False, server_default=sa.text("'pending'")),
        sa.Column("ai_reason", sa.Text(), nullable=True),
        sa.Column("ai_next_action", sa.String(length=200), nullable=True),
        sa.Column("ai_score", sa.Integer(), nullable=True),
        sa.Column("due_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "status IN ('pending','in_progress','completed','cancelled','overdue')",
            name="ck_automation_tasks__status",
        ),
        sa.CheckConstraint(
            "priority IN ('low','medium','high','critical')",
            name="ck_automation_tasks__priority",
        ),
        sa.CheckConstraint(
            "task_type IN ("
            "'follow_up','call','proposal','meeting','recovery',"
            "'alert','win_log','loss_log','pipeline_event',"
            "'inventory_check','order_risk')",
            name="ck_automation_tasks__task_type",
        ),
    )
    op.create_index(
        "idx_automation_tasks__empresa_id_status_due",
        "automation_tasks",
        ["empresa_id", "status", "due_date"],
    )
    op.create_index(
        "idx_automation_tasks__empresa_id_priority",
        "automation_tasks",
        ["empresa_id", "priority"],
    )
    op.create_index(
        "idx_automation_tasks__empresa_id_rule_id",
        "automation_tasks",
        ["empresa_id", "rule_id"],
    )
    op.create_index(
        "idx_automation_tasks__empresa_id_customer",
        "automation_tasks",
        ["empresa_id", "customer_id"],
    )
    op.create_index(
        "idx_automation_tasks__empresa_id_pipeline_item",
        "automation_tasks",
        ["empresa_id", "pipeline_item_id"],
    )
    op.create_index(
        "idx_automation_tasks__empresa_id_due_date",
        "automation_tasks",
        ["empresa_id", "due_date"],
    )

    # -------------------------------------------------------------------------
    # automation_events
    # -------------------------------------------------------------------------
    op.create_table(
        "automation_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("empresa_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("empresas.id", ondelete="RESTRICT"), nullable=False, index=True),
        sa.Column(
            "rule_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("automation_rules.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("rule_key", sa.String(length=64), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("entity_type", sa.String(length=32), nullable=False, server_default=sa.text("'none'")),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("severity", sa.String(length=16), nullable=False, server_default=sa.text("'info'")),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "severity IN ('info','warning','critical')",
            name="ck_automation_events__severity",
        ),
        sa.CheckConstraint(
            "entity_type IN ("
            "'customer','pipeline_item','conversation','order',"
            "'inventory_item','none')",
            name="ck_automation_events__entity_type",
        ),
    )
    op.create_index(
        "idx_automation_events__empresa_id_created_at",
        "automation_events",
        ["empresa_id", "created_at"],
    )
    op.create_index(
        "idx_automation_events__empresa_id_rule_key",
        "automation_events",
        ["empresa_id", "rule_key"],
    )
    op.create_index(
        "idx_automation_events__empresa_id_entity",
        "automation_events",
        ["empresa_id", "entity_type", "entity_id"],
    )


def downgrade() -> None:
    op.drop_index("idx_automation_events__empresa_id_entity", table_name="automation_events")
    op.drop_index("idx_automation_events__empresa_id_rule_key", table_name="automation_events")
    op.drop_index("idx_automation_events__empresa_id_created_at", table_name="automation_events")
    op.drop_table("automation_events")

    op.drop_index("idx_automation_tasks__empresa_id_due_date", table_name="automation_tasks")
    op.drop_index("idx_automation_tasks__empresa_id_pipeline_item", table_name="automation_tasks")
    op.drop_index("idx_automation_tasks__empresa_id_customer", table_name="automation_tasks")
    op.drop_index("idx_automation_tasks__empresa_id_rule_id", table_name="automation_tasks")
    op.drop_index("idx_automation_tasks__empresa_id_priority", table_name="automation_tasks")
    op.drop_index("idx_automation_tasks__empresa_id_status_due", table_name="automation_tasks")
    op.drop_table("automation_tasks")

    op.drop_index("idx_automation_rules__empresa_id_enabled", table_name="automation_rules")
    op.drop_table("automation_rules")
