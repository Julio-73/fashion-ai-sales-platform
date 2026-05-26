import logging
from uuid import UUID

from app.ai.schemas.ai_schemas import (
    ContextData,
    ContextResponse,
    ConversationStage,
    CustomerProfileRef,
)

logger = logging.getLogger("ai_sales_agent.ai.context")


class ConversationContextBuilder:
    async def build(
        self,
        *,
        empresa_id: UUID,
        customer_id: UUID,
        conversation_id: UUID,
    ) -> ContextResponse:
        customer = await self._get_customer_profile(empresa_id, customer_id)
        messages = await self._get_recent_messages(empresa_id, conversation_id)
        stage = await self._determine_stage(customer, messages)
        interests = await self._get_product_interests(empresa_id, customer_id)

        context = ContextData(
            customer=customer,
            recent_messages=messages,
            conversation_stage=stage,
            product_interests=interests,
        )
        return ContextResponse(context=context)

    async def _get_customer_profile(
        self, empresa_id: UUID, customer_id: UUID
    ) -> CustomerProfileRef:
        return CustomerProfileRef(
            customer_id=customer_id,
            customer_name="",
            lead_score=0.0,
            tags=[],
        )

    async def _get_recent_messages(
        self, empresa_id: UUID, conversation_id: UUID
    ) -> list[str]:
        return []

    async def _determine_stage(
        self, customer: CustomerProfileRef, messages: list[str]
    ) -> ConversationStage:
        if not messages:
            return ConversationStage.new
        if customer.lead_score >= 0.8:
            return ConversationStage.closing
        if customer.lead_score >= 0.5:
            return ConversationStage.negotiation
        return ConversationStage.active

    async def _get_product_interests(
        self, empresa_id: UUID, customer_id: UUID
    ) -> list[str]:
        return []
