"""Repository layer for the WhatsApp Business integration.

Each method is intentionally narrow and async. Higher-level orchestration
(tenant checks, customer creation, conversation reuse) lives in
``service.py``.
"""
from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.whatsapp.models import WhatsappAccount, WhatsappMessage, WhatsappWebhook


class WhatsappAccountRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, *, empresa_id: UUID, **fields: Any) -> WhatsappAccount:
        account = WhatsappAccount(empresa_id=empresa_id, **fields)
        self._session.add(account)
        await self._session.flush()
        return account

    async def get_by_id(
        self, *, empresa_id: UUID, account_id: UUID
    ) -> WhatsappAccount | None:
        result = await self._session.execute(
            select(WhatsappAccount).where(
                WhatsappAccount.empresa_id == empresa_id,
                WhatsappAccount.id == account_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_phone_number_id(
        self, *, phone_number_id: str
    ) -> WhatsappAccount | None:
        """Lookup is *cross-tenant* on purpose: the webhook fires before
        we know which company the payload belongs to, so we discover the
        tenant by the phone number id (which is globally unique per Meta
        business account).
        """
        result = await self._session.execute(
            select(WhatsappAccount).where(
                WhatsappAccount.phone_number_id == phone_number_id
            )
        )
        return result.scalar_one_or_none()

    async def list_active(
        self, *, empresa_id: UUID
    ) -> Sequence[WhatsappAccount]:
        result = await self._session.execute(
            select(WhatsappAccount)
            .where(
                WhatsappAccount.empresa_id == empresa_id,
                WhatsappAccount.is_active.is_(True),
            )
            .order_by(WhatsappAccount.created_at.asc())
        )
        return result.scalars().all()

    async def list_all(self, *, empresa_id: UUID) -> Sequence[WhatsappAccount]:
        result = await self._session.execute(
            select(WhatsappAccount)
            .where(WhatsappAccount.empresa_id == empresa_id)
            .order_by(WhatsappAccount.created_at.asc())
        )
        return result.scalars().all()

    async def update(
        self,
        *,
        account: WhatsappAccount,
        payload: dict[str, Any],
    ) -> WhatsappAccount:
        for key, value in payload.items():
            if value is None:
                continue
            setattr(account, key, value)
        account.updated_at = datetime.now(UTC)
        await self._session.flush()
        return account

    async def soft_delete(self, *, account: WhatsappAccount) -> None:
        account.is_active = False
        account.updated_at = datetime.now(UTC)
        await self._session.flush()

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()


class WhatsappWebhookRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def record(
        self,
        *,
        empresa_id: UUID | None,
        phone_number_id: str | None,
        event_type: str,
        payload: dict[str, Any],
        received_at: datetime | None = None,
    ) -> WhatsappWebhook:
        row = WhatsappWebhook(
            empresa_id=empresa_id,
            phone_number_id=phone_number_id,
            event_type=event_type,
            payload=payload,
            received_at=received_at or datetime.now(UTC),
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def list_recent(
        self,
        *,
        empresa_id: UUID,
        limit: int,
        offset: int,
    ) -> tuple[Sequence[WhatsappWebhook], int]:
        base = select(WhatsappWebhook).where(WhatsappWebhook.empresa_id == empresa_id)
        count_q = select(func.count()).select_from(base.subquery())
        total = int((await self._session.execute(count_q)).scalar_one())
        result = await self._session.execute(
            base.order_by(WhatsappWebhook.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all(), total

    async def mark_processed(
        self,
        *,
        webhook: WhatsappWebhook,
        error: str | None = None,
    ) -> None:
        webhook.processed = error is None
        webhook.error = error
        await self._session.flush()

    async def count_since(
        self,
        *,
        empresa_id: UUID,
        since: datetime,
        only_failed: bool = False,
    ) -> int:
        query = select(func.count()).select_from(WhatsappWebhook).where(
            WhatsappWebhook.empresa_id == empresa_id,
            WhatsappWebhook.created_at >= since,
        )
        if only_failed:
            query = query.where(WhatsappWebhook.error.is_not(None))
        result = await self._session.execute(query)
        return int(result.scalar_one() or 0)

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()


class WhatsappMessageRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, *, empresa_id: UUID, **fields: Any) -> WhatsappMessage:
        row = WhatsappMessage(empresa_id=empresa_id, **fields)
        self._session.add(row)
        await self._session.flush()
        return row

    async def update_status(
        self,
        *,
        message_id: UUID,
        empresa_id: UUID,
        status: str,
        wa_message_id: str | None = None,
        error: str | None = None,
    ) -> None:
        values: dict[str, Any] = {
            "status": status,
            "updated_at": datetime.now(UTC),
        }
        if wa_message_id is not None:
            values["wa_message_id"] = wa_message_id
        if error is not None:
            values["error"] = error
        await self._session.execute(
            update(WhatsappMessage)
            .where(
                WhatsappMessage.id == message_id,
                WhatsappMessage.empresa_id == empresa_id,
            )
            .values(**values)
        )

    async def list(
        self,
        *,
        empresa_id: UUID,
        limit: int,
        offset: int,
        direction: str | None = None,
    ) -> tuple[Sequence[WhatsappMessage], int]:
        base = select(WhatsappMessage).where(WhatsappMessage.empresa_id == empresa_id)
        if direction:
            base = base.where(WhatsappMessage.direction == direction)
        total = int(
            (
                await self._session.execute(
                    select(func.count()).select_from(base.subquery())
                )
            ).scalar_one()
        )
        result = await self._session.execute(
            base.order_by(WhatsappMessage.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all(), total

    async def counts_since(
        self,
        *,
        empresa_id: UUID,
        since: datetime,
    ) -> dict[str, int]:
        rows = (
            await self._session.execute(
                select(
                    WhatsappMessage.direction,
                    WhatsappMessage.status,
                    func.count(),
                )
                .where(
                    WhatsappMessage.empresa_id == empresa_id,
                    WhatsappMessage.created_at >= since,
                )
                .group_by(WhatsappMessage.direction, WhatsappMessage.status)
            )
        ).all()
        out: dict[str, int] = {
            "inbound": 0,
            "outbound": 0,
            "delivered": 0,
            "failed": 0,
            "pending": 0,
        }
        for direction, status, count in rows:
            if direction == "inbound":
                out["inbound"] += int(count)
            elif direction == "outbound":
                out["outbound"] += int(count)
            if status == "delivered":
                out["delivered"] += int(count)
            elif status == "failed":
                out["failed"] += int(count)
            elif status == "pending":
                out["pending"] += int(count)
        return out

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()
