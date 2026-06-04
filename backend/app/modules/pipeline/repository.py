"""Repository layer — pure data access for ``sales_pipeline_items``.

This module never raises business errors. It returns ``None`` for
missing rows and never enforces tenant isolation at the SQL level —
the service layer is responsible for scoping by ``empresa_id``.
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Sequence
from uuid import UUID

from sqlalchemy import and_, delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.pipeline.models import (
    CLOSED_STAGES,
    OPEN_STAGES,
    SalesPipelineItem,
    is_valid_stage,
)


class PipelineRepository:
    """Async data-access object for ``sales_pipeline_items``."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------
    async def list_items(
        self,
        *,
        empresa_id: UUID,
        stage: str | None = None,
        customer_id: UUID | None = None,
        is_open: bool | None = None,
        search: str | None = None,
        limit: int = 200,
        offset: int = 0,
    ) -> Sequence[SalesPipelineItem]:
        stmt = select(SalesPipelineItem).where(SalesPipelineItem.empresa_id == empresa_id)
        if stage is not None and is_valid_stage(stage):
            stmt = stmt.where(SalesPipelineItem.stage == stage)
        if customer_id is not None:
            stmt = stmt.where(SalesPipelineItem.customer_id == customer_id)
        if is_open is True:
            stmt = stmt.where(SalesPipelineItem.stage.in_(tuple(OPEN_STAGES)))
        elif is_open is False:
            stmt = stmt.where(SalesPipelineItem.stage.in_(tuple(CLOSED_STAGES)))
        if search:
            like = f"%{search.lower()}%"
            stmt = stmt.where(func.lower(SalesPipelineItem.title).like(like))
        stmt = (
            stmt.order_by(
                SalesPipelineItem.stage,
                SalesPipelineItem.position,
                SalesPipelineItem.last_activity_at.desc(),
            )
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get(self, empresa_id: UUID, item_id: UUID) -> SalesPipelineItem | None:
        stmt = select(SalesPipelineItem).where(
            and_(
                SalesPipelineItem.empresa_id == empresa_id,
                SalesPipelineItem.id == item_id,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def count_by_stage(self, empresa_id: UUID) -> dict[str, int]:
        stmt = select(SalesPipelineItem.stage, func.count(SalesPipelineItem.id)).where(
            SalesPipelineItem.empresa_id == empresa_id
        ).group_by(SalesPipelineItem.stage)
        result = await self.session.execute(stmt)
        out: dict[str, int] = {}
        for stage, count in result.all():
            out[stage] = int(count)
        return out

    async def sum_value_by_stage(self, empresa_id: UUID) -> dict[str, float]:
        stmt = select(
            SalesPipelineItem.stage,
            func.coalesce(func.sum(SalesPipelineItem.estimated_value), 0),
        ).where(
            SalesPipelineItem.empresa_id == empresa_id
        ).group_by(SalesPipelineItem.stage)
        result = await self.session.execute(stmt)
        return {stage: float(value or 0) for stage, value in result.all()}

    async def aggregate_metrics(
        self, empresa_id: UUID
    ) -> dict[str, Any]:
        """Return aggregate counters used by ``/pipeline/metrics``."""
        # Open vs closed counts
        cnt_stmt = select(
            SalesPipelineItem.stage,
            func.count(SalesPipelineItem.id),
            func.coalesce(func.sum(SalesPipelineItem.estimated_value), 0),
        ).where(
            SalesPipelineItem.empresa_id == empresa_id
        ).group_by(SalesPipelineItem.stage)
        result = await self.session.execute(cnt_stmt)

        counts: dict[str, int] = {}
        values: dict[str, float] = {}
        for stage, count, value in result.all():
            counts[stage] = int(count)
            values[stage] = float(value or 0)

        # Weighted value
        w_stmt = select(
            func.coalesce(
                func.sum(
                    SalesPipelineItem.estimated_value
                    * SalesPipelineItem.probability
                    / 100.0
                ),
                0,
            )
        ).where(
            SalesPipelineItem.empresa_id == empresa_id,
            SalesPipelineItem.stage.in_(tuple(OPEN_STAGES)),
        )
        weighted = float((await self.session.execute(w_stmt)).scalar() or 0)

        # Max days in current stage across all open deals
        # We use stage_entered_at as a proxy for "entered current stage".
        # ``func.now() - stage_entered_at`` gives an INTERVAL which we
        # extract with ``EXTRACT(EPOCH FROM …)`` divided by 86400.
        days_expr = func.extract(
            "epoch", func.now() - SalesPipelineItem.stage_entered_at
        ) / 86400.0
        max_stmt = select(
            func.coalesce(func.max(days_expr), 0)
        ).where(
            SalesPipelineItem.empresa_id == empresa_id,
            SalesPipelineItem.stage.in_(tuple(OPEN_STAGES)),
        )
        oldest = float((await self.session.execute(max_stmt)).scalar() or 0)

        return {
            "counts": counts,
            "values": values,
            "weighted_open": weighted,
            "oldest_in_stage_days": int(oldest),
        }

    async def list_for_funnel(self, empresa_id: UUID) -> Sequence[SalesPipelineItem]:
        stmt = select(SalesPipelineItem).where(
            SalesPipelineItem.empresa_id == empresa_id
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------
    async def create(
        self,
        *,
        empresa_id: UUID,
        customer_id: UUID | None,
        conversation_id: UUID | None,
        order_id: UUID | None,
        title: str,
        estimated_value: Decimal,
        probability: int,
        stage: str,
        notes: str | None,
        channel: str | None,
        is_vip: bool,
        position: int,
    ) -> SalesPipelineItem:
        now = datetime.utcnow()
        item = SalesPipelineItem(
            empresa_id=empresa_id,
            customer_id=customer_id,
            conversation_id=conversation_id,
            order_id=order_id,
            title=title,
            estimated_value=estimated_value,
            probability=probability,
            stage=stage,
            notes=notes,
            channel=channel,
            is_vip=is_vip,
            position=position,
            stage_entered_at=now,
            last_activity_at=now,
        )
        self.session.add(item)
        await self.session.flush()
        return item

    async def update(
        self,
        *,
        item: SalesPipelineItem,
        changes: dict[str, Any],
    ) -> SalesPipelineItem:
        if not changes:
            return item
        for key, value in changes.items():
            setattr(item, key, value)
        item.last_activity_at = datetime.utcnow()
        item.updated_at = datetime.utcnow()
        await self.session.flush()
        return item

    async def move_stage(
        self,
        *,
        item: SalesPipelineItem,
        target_stage: str,
        probability: int | None,
        notes: str | None,
        won_reason: str | None,
        lost_reason: str | None,
    ) -> SalesPipelineItem:
        now = datetime.utcnow()
        item.stage = target_stage
        item.stage_entered_at = now
        item.last_activity_at = now
        item.updated_at = now
        if probability is not None:
            item.probability = probability
        if notes is not None:
            item.notes = notes
        if target_stage == "won" and won_reason is not None:
            item.won_reason = won_reason
            item.lost_reason = None
        if target_stage == "lost" and lost_reason is not None:
            item.lost_reason = lost_reason
            item.won_reason = None
        await self.session.flush()
        return item

    async def soft_delete(self, item: SalesPipelineItem) -> None:
        # No soft-delete column in the model — we hard delete. This is
        # acceptable because (a) the original ``clientes`` and orders
        # survive, (b) the kanban only needs current state, and
        # (c) we keep an audit trail in the application logs.
        await self.session.delete(item)
        await self.session.flush()

    async def delete_for_empresa(self, empresa_id: UUID) -> int:
        stmt = delete(SalesPipelineItem).where(
            SalesPipelineItem.empresa_id == empresa_id
        )
        result = await self.session.execute(stmt)
        return int(result.rowcount or 0)

    async def bump_position(self, item: SalesPipelineItem, new_position: int) -> None:
        item.position = new_position
        item.updated_at = datetime.utcnow()
        item.last_activity_at = datetime.utcnow()
        await self.session.flush()


__all__ = ["PipelineRepository"]
