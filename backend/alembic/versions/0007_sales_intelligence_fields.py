"""add lead_score and priority to clientes

Revision ID: 0007_sales_intelligence_fields
Revises: 0006_cust_conv_metrics
Create Date: 2026-05-25
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0007_sales_intelligence_fields"
down_revision: str | None = "0006_cust_conv_metrics"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "clientes",
        sa.Column("lead_score", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "clientes",
        sa.Column("priority", sa.String(length=16), nullable=False, server_default="cold"),
    )


def downgrade() -> None:
    op.drop_column("clientes", "priority")
    op.drop_column("clientes", "lead_score")
