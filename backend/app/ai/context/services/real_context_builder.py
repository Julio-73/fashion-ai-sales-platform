import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.context.repositories.conversation_context_repository import (
    ConversationContextRepository,
)
from app.ai.context.repositories.product_context_repository import (
    ProductContextRepository,
)
from app.ai.context.services.behavioral_profile_service import (
    BehavioralProfileService,
)
from app.ai.context.services.customer_memory_service import CustomerMemoryService
from app.ai.schemas.ai_schemas import (
    ConversationHistory,
    MessageHistoryItem,
    ProductContextDetail,
    ProductInterest,
    RichContextData,
    RichCustomerProfile,
)

logger = logging.getLogger("ai_sales_agent.ai.context.services.real_context_builder")


class RealContextBuilder:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._customer_memory = CustomerMemoryService(session)
        self._conversation_repo = ConversationContextRepository(session)
        self._product_repo = ProductContextRepository(session)
        self._behavioral_service = BehavioralProfileService(session)

    async def build_rich_context(
        self,
        *,
        empresa_id: UUID,
        customer_id: UUID,
        conversation_id: UUID,
    ) -> RichContextData:
        customer = await self._customer_memory.build_profile(
            empresa_id=empresa_id, customer_id=customer_id
        )
        conversation = await self._build_conversation_history(
            empresa_id=empresa_id, conversation_id=conversation_id
        )
        products = await self._build_product_context(
            empresa_id=empresa_id, customer_id=customer_id
        )
        sales = await self._behavioral_service.build_sales_context(
            empresa_id=empresa_id, customer_id=customer_id
        )
        return RichContextData(
            customer=customer,
            conversation=conversation,
            products=products,
            sales=sales,
        )

    async def _build_conversation_history(
        self, *, empresa_id: UUID, conversation_id: UUID
    ) -> ConversationHistory:
        messages = await self._conversation_repo.get_recent_messages_core(
            empresa_id=empresa_id, conversation_id=conversation_id, limit=20
        )
        detected_intents = await self._conversation_repo.get_detected_intents(
            empresa_id=empresa_id, conversation_id=conversation_id
        )
        sentiment_history = await self._conversation_repo.get_sentiment_history(
            empresa_id=empresa_id, conversation_id=conversation_id
        )
        has_escalations = await self._conversation_repo.has_escalations(
            empresa_id=empresa_id, conversation_id=conversation_id
        )
        avg_response_time = await self._conversation_repo.compute_average_response_time(
            empresa_id=empresa_id, conversation_id=conversation_id
        )
        conv = await self._conversation_repo.get_conversation_core(
            empresa_id=empresa_id, conversation_id=conversation_id
        )
        total_messages = len(messages)

        return ConversationHistory(
            conversation_id=conversation_id,
            messages=[
                MessageHistoryItem(
                    role=m.get("sender", m.get("role", "")),
                    content=m["content"],
                    created_at=m.get("created_at"),
                )
                for m in messages
            ],
            detected_intents=detected_intents,
            sentiment_history=sentiment_history,
            has_escalations=has_escalations,
            has_handoffs=has_escalations,
            average_response_time_minutes=avg_response_time,
            total_messages=total_messages,
            status=conv.status if conv else "active",
        )

    async def _build_product_context(
        self, *, empresa_id: UUID, customer_id: UUID
    ) -> ProductContextDetail:
        viewed = await self._product_repo.get_products_viewed_by_customer(
            empresa_id=empresa_id, customer_id=customer_id
        )
        asked = await self._product_repo.get_products_asked_by_customer(
            empresa_id=empresa_id, customer_id=customer_id
        )
        categories = await self._product_repo.get_frequent_categories(
            empresa_id=empresa_id, customer_id=customer_id
        )
        styles = await self._product_repo.get_preferred_styles_from_memory(
            empresa_id=empresa_id, customer_id=customer_id
        )
        upsell = await self._product_repo.find_upsell_candidates(
            empresa_id=empresa_id, customer_id=customer_id
        )
        total = await self._product_repo.get_total_products_queried(
            empresa_id=empresa_id, customer_id=customer_id
        )

        return ProductContextDetail(
            products_viewed=[
                ProductInterest(
                    product_id=p.get("product_id"),
                    product_name=p["product_name"],
                    category=p.get("category", ""),
                    viewed_count=p.get("viewed_count", 0),
                    stock_available=p.get("stock_available", 0),
                    has_stock=p.get("has_stock", False),
                    price=p.get("price", 0.0),
                )
                for p in viewed
            ],
            products_asked=[
                ProductInterest(
                    product_id=p.get("product_id"),
                    product_name=p["product_name"],
                    category=p.get("category", ""),
                    asked_count=p.get("asked_count", 0),
                    price=p.get("price", 0.0),
                )
                for p in asked
            ],
            frequent_categories=categories,
            preferred_styles=styles,
            upsell_candidates=[
                ProductInterest(
                    product_id=p.get("product_id"),
                    product_name=p["product_name"],
                    category=p.get("category", ""),
                    stock_available=p.get("stock_available", 0),
                    has_stock=p.get("has_stock", False),
                    price=p.get("price", 0.0),
                )
                for p in upsell
            ],
            total_products_queried=total,
        )
