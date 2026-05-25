"""CRM Bridge Service — connects Conversations Core → CRM.

Responsible for:
- Updating customer activity (last_interaction_at, conversation_count, last_conversation_id)
- Auto conversation status suggestion (e.g., reactivate closed conversations)
- Extensible tag evaluation (pluggable evaluators for AI-powered auto-tagging)
"""

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.customers.repository import CustomerRepository
from app.services.tag_evaluator import DEFAULT_EVALUATOR, TagEvaluationContext, TagEvaluator


@dataclass
class SyncResult:
    should_reactivate: bool = False


class CrmBridgeService:
    def __init__(
        self,
        session: AsyncSession,
        customer_repository: CustomerRepository,
        tag_evaluator: TagEvaluator | None = None,
    ) -> None:
        self._session = session
        self._customer_repo = customer_repository
        self._tag_evaluator = tag_evaluator or DEFAULT_EVALUATOR

    async def sync_after_message(
        self,
        *,
        empresa_id: UUID,
        customer_id: UUID,
        conversation_id: UUID,
        conversation_status: str,
        message_content: str,
        message_sender: str,
    ) -> SyncResult:
        customer = await self._customer_repo.get_by_id(
            empresa_id=empresa_id, customer_id=customer_id
        )
        if customer is None:
            return SyncResult()

        now = datetime.now(UTC)

        customer.last_interaction_at = now
        customer.last_conversation_id = conversation_id

        should_reactivate = conversation_status == "closed"

        tag_context = TagEvaluationContext(
            empresa_id=empresa_id,
            customer_id=customer_id,
            conversation_id=conversation_id,
            message_content=message_content,
            message_sender=message_sender,
            conversation_status="active" if should_reactivate else conversation_status,
            lead_status=customer.lead_status,
            existing_tags=tuple(customer.tags),
        )
        suggested_tags = await self._tag_evaluator.evaluate(tag_context)
        if suggested_tags:
            existing = set(customer.tags)
            for tag in suggested_tags:
                cleaned = tag.strip()[:48]
                if cleaned and cleaned not in existing:
                    customer.tags.append(cleaned)
                    existing.add(cleaned)

        await self._session.flush()
        return SyncResult(should_reactivate=should_reactivate)

    async def increment_conversation_count(
        self,
        *,
        empresa_id: UUID,
        customer_id: UUID,
    ) -> None:
        customer = await self._customer_repo.get_by_id(
            empresa_id=empresa_id, customer_id=customer_id
        )
        if customer is None:
            return

        customer.conversation_count += 1
        await self._session.flush()

    async def sync_conversation_status(
        self,
        *,
        empresa_id: UUID,
        customer_id: UUID,
        conversation_status: str,
    ) -> None:
        customer = await self._customer_repo.get_by_id(
            empresa_id=empresa_id, customer_id=customer_id
        )
        if customer is None:
            return

        if conversation_status == "converted" and customer.lead_status != "won":
            customer.lead_status = "won"
            existing_lower = [t.strip().lower() for t in customer.tags]
            if "won" not in existing_lower and "ganado" not in existing_lower:
                customer.tags.append("won")

        await self._session.flush()
