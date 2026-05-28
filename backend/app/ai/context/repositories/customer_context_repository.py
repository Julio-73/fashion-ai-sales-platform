import logging
from collections.abc import Sequence
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.conversations.models import ConversationCore, MessageCore
from app.modules.customers.models import Cliente
from app.modules.products.models import ProductVariant, Producto

logger = logging.getLogger("ai_sales_agent.ai.context.repositories.customer")


class CustomerContextRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_customer(self, *, empresa_id: UUID, customer_id: UUID) -> Cliente | None:
        result = await self._session.execute(
            select(Cliente).where(
                Cliente.empresa_id == empresa_id,
                Cliente.id == customer_id,
                Cliente.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def get_customer_interaction_count(
        self, *, empresa_id: UUID, customer_id: UUID
    ) -> int:
        result = await self._session.execute(
            select(func.count()).select_from(
                select(ConversationCore)
                .where(
                    ConversationCore.empresa_id == empresa_id,
                    ConversationCore.customer_id == customer_id,
                )
                .subquery()
            )
        )
        return int(result.scalar_one())

    async def get_customer_message_count(
        self, *, empresa_id: UUID, customer_id: UUID
    ) -> int:
        result = await self._session.execute(
            select(func.count()).select_from(
                select(MessageCore)
                .join(ConversationCore, MessageCore.conversation_id == ConversationCore.id)
                .where(
                    ConversationCore.empresa_id == empresa_id,
                    ConversationCore.customer_id == customer_id,
                )
                .subquery()
            )
        )
        return int(result.scalar_one())

    async def get_favorite_categories(
        self, *, empresa_id: UUID, customer_id: UUID, limit: int = 5
    ) -> list[str]:
        raw = text("""
            SELECT p.category, COUNT(*) AS cnt
            FROM messages_core mc
            JOIN conversations_core cc ON cc.id = mc.conversation_id
            JOIN productos p ON 1=1
            WHERE cc.empresa_id = :eid
              AND cc.customer_id = :cid
              AND p.empresa_id = :eid
              AND p.deleted_at IS NULL
              AND LOWER(mc.content) LIKE '%' || LOWER(p.name) || '%'
            GROUP BY p.category
            ORDER BY cnt DESC
            LIMIT :lim
        """)
        result = await self._session.execute(
            raw, {"eid": empresa_id, "cid": customer_id, "lim": limit}
        )
        return [row.category for row in result if row.category]

    async def get_preferred_attributes(
        self, *, empresa_id: UUID, customer_id: UUID
    ) -> dict[str, list[str]]:
        messages_result = await self._session.execute(
            select(MessageCore.content)
            .join(ConversationCore, MessageCore.conversation_id == ConversationCore.id)
            .where(
                ConversationCore.empresa_id == empresa_id,
                ConversationCore.customer_id == customer_id,
            )
            .limit(500)
        )
        messages = [row.content for row in messages_result if row.content]
        colors = set()
        sizes = set()
        color_keywords = {"rojo", "azul", "negro", "blanco", "verde", "amarillo",
                          "rosado", "gris", "naranja", "morado", "beige", "marrón"}
        size_keywords = {"xs", "s", "m", "l", "xl", "xxl", "talla s", "talla m",
                         "talla l", "talla xl"}
        for msg in messages:
            lower = msg.lower()
            for c in color_keywords:
                if c in lower:
                    colors.add(c)
            for s in size_keywords:
                if s in lower:
                    sizes.add(s.replace("talla ", ""))
        return {
            "colors": sorted(colors),
            "sizes": sorted(sizes),
        }

    async def get_purchase_history_summary(
        self, *, empresa_id: UUID, customer_id: UUID
    ) -> dict:
        raw = text("""
            SELECT
                COUNT(*) AS total_orders,
                COALESCE(AVG(p.base_price), 0) AS avg_order_value,
                COALESCE(SUM(p.base_price), 0) AS total_lifetime_value
            FROM conversations_core cc
            JOIN clientes cl ON cl.id = cc.customer_id
            LEFT JOIN productos p ON 1=1
            WHERE cc.empresa_id = :eid
              AND cc.customer_id = :cid
              AND cl.deleted_at IS NULL
              AND p.empresa_id = :eid
              AND p.deleted_at IS NULL
              AND cl.lead_status = 'won'
        """)
        result = await self._session.execute(
            raw, {"eid": empresa_id, "cid": customer_id}
        )
        row = result.one_or_none()
        if row:
            return {
                "total_orders": int(row.total_orders) if row.total_orders else 0,
                "avg_order_value": float(row.avg_order_value) if row.avg_order_value else 0.0,
                "total_lifetime_value": float(row.total_lifetime_value) if row.total_lifetime_value else 0.0,
            }
        return {"total_orders": 0, "avg_order_value": 0.0, "total_lifetime_value": 0.0}

    async def get_customer_tags(self, *, empresa_id: UUID, customer_id: UUID) -> list[str]:
        customer = await self.get_customer(empresa_id=empresa_id, customer_id=customer_id)
        return customer.tags if customer else []

    async def get_lead_score_evolution(
        self, *, empresa_id: UUID, customer_id: UUID
    ) -> list[dict]:
        raw = text("""
            SELECT lead_score, updated_at
            FROM clientes
            WHERE empresa_id = :eid AND id = :cid AND deleted_at IS NULL
            ORDER BY updated_at DESC
            LIMIT 10
        """)
        result = await self._session.execute(
            raw, {"eid": empresa_id, "cid": customer_id}
        )
        return [
            {"score": row.lead_score, "timestamp": row.updated_at.isoformat() if row.updated_at else None}
            for row in result
        ]
