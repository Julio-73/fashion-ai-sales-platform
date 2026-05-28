import logging
from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.modules.products.models import ProductVariant, Producto
from app.smart_sales.product_context import ProductContextEngine

logger = logging.getLogger("ai_sales_agent.ai.context.repositories.product")


class ProductContextRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._context_engine = ProductContextEngine(session)

    async def get_products_viewed_by_customer(
        self, *, empresa_id: UUID, customer_id: UUID, limit: int = 10
    ) -> list[dict]:
        raw = text("""
            SELECT
                p.id, p.name, p.category, p.base_price,
                COUNT(*) AS mention_count
            FROM messages_core mc
            JOIN conversations_core cc ON cc.id = mc.conversation_id
            JOIN productos p ON p.empresa_id = cc.empresa_id
            WHERE cc.empresa_id = :eid
              AND cc.customer_id = :cid
              AND p.deleted_at IS NULL
              AND LOWER(mc.content) LIKE '%' || LOWER(p.name) || '%'
            GROUP BY p.id, p.name, p.category, p.base_price
            ORDER BY mention_count DESC
            LIMIT :lim
        """)
        result = await self._session.execute(
            raw, {"eid": empresa_id, "cid": customer_id, "lim": limit}
        )
        products = []
        for row in result:
            stock_result = await self._session.execute(
                select(func.coalesce(func.sum(ProductVariant.stock - ProductVariant.reserved_stock), 0))
                .where(
                    ProductVariant.empresa_id == empresa_id,
                    ProductVariant.product_id == row.id,
                    ProductVariant.deleted_at.is_(None),
                )
            )
            available_stock = int(stock_result.scalar())
            products.append({
                "product_id": row.id,
                "product_name": row.name,
                "category": row.category or "",
                "viewed_count": int(row.mention_count),
                "stock_available": available_stock,
                "has_stock": available_stock > 0,
                "price": float(row.base_price) if row.base_price else 0.0,
            })
        return products

    async def get_products_asked_by_customer(
        self, *, empresa_id: UUID, customer_id: UUID, limit: int = 10
    ) -> list[dict]:
        raw = text("""
            SELECT
                p.id, p.name, p.category, p.base_price,
                COUNT(*) AS ask_count
            FROM messages_core mc
            JOIN conversations_core cc ON cc.id = mc.conversation_id
            JOIN productos p ON p.empresa_id = cc.empresa_id
            WHERE cc.empresa_id = :eid
              AND cc.customer_id = :cid
              AND p.deleted_at IS NULL
              AND (
                  LOWER(mc.content) LIKE '%' || LOWER(p.name) || '%'
                  OR LOWER(mc.content) LIKE '%' || LOWER(p.category) || '%'
              )
              AND mc.sender = 'client'
            GROUP BY p.id, p.name, p.category, p.base_price
            ORDER BY ask_count DESC
            LIMIT :lim
        """)
        result = await self._session.execute(
            raw, {"eid": empresa_id, "cid": customer_id, "lim": limit}
        )
        return [
            {
                "product_id": row.id,
                "product_name": row.name,
                "category": row.category or "",
                "asked_count": int(row.ask_count),
                "price": float(row.base_price) if row.base_price else 0.0,
            }
            for row in result
        ]

    async def get_frequent_categories(
        self, *, empresa_id: UUID, customer_id: UUID, limit: int = 5
    ) -> list[str]:
        raw = text("""
            SELECT p.category, COUNT(*) AS cnt
            FROM messages_core mc
            JOIN conversations_core cc ON cc.id = mc.conversation_id
            JOIN productos p ON p.empresa_id = cc.empresa_id
            WHERE cc.empresa_id = :eid
              AND cc.customer_id = :cid
              AND p.deleted_at IS NULL
              AND p.category IS NOT NULL
              AND (
                  LOWER(mc.content) LIKE '%' || LOWER(p.category) || '%'
                  OR LOWER(mc.content) LIKE '%' || LOWER(p.name) || '%'
              )
            GROUP BY p.category
            ORDER BY cnt DESC
            LIMIT :lim
        """)
        result = await self._session.execute(
            raw, {"eid": empresa_id, "cid": customer_id, "lim": limit}
        )
        return [row.category for row in result]

    async def get_preferred_styles_from_memory(
        self, *, empresa_id: UUID, customer_id: UUID
    ) -> list[str]:
        from app.ai.memory.models import ConversationMemory
        result = await self._session.execute(
            select(ConversationMemory.extracted_styles)
            .where(
                ConversationMemory.empresa_id == empresa_id,
                ConversationMemory.customer_id == customer_id,
            )
            .order_by(ConversationMemory.created_at.desc())
            .limit(5)
        )
        styles = set()
        for row in result:
            if row.extracted_styles:
                styles.update(row.extracted_styles)
        return list(styles)

    async def find_upsell_candidates(
        self, *, empresa_id: UUID, customer_id: UUID, limit: int = 5
    ) -> list[dict]:
        categories = await self.get_frequent_categories(
            empresa_id=empresa_id, customer_id=customer_id, limit=3
        )
        if not categories:
            return []
        result = await self._session.execute(
            select(Producto)
            .options(joinedload(Producto.variants))
            .where(
                Producto.empresa_id == empresa_id,
                Producto.category.in_(categories),
                Producto.status == "active",
                Producto.deleted_at.is_(None),
            )
            .limit(limit)
        )
        products: Sequence[Producto] = result.unique().scalars().all()
        upsell = []
        for p in products:
            available_stock = sum(
                v.stock - v.reserved_stock for v in p.variants if v.deleted_at is None
            )
            upsell.append({
                "product_id": p.id,
                "product_name": p.name,
                "category": p.category or "",
                "price": float(p.base_price) if p.base_price else 0.0,
                "stock_available": available_stock,
                "has_stock": available_stock > 0,
            })
        return upsell

    async def get_total_products_queried(
        self, *, empresa_id: UUID, customer_id: UUID
    ) -> int:
        raw = text("""
            SELECT COUNT(DISTINCT p.id) AS total
            FROM messages_core mc
            JOIN conversations_core cc ON cc.id = mc.conversation_id
            JOIN productos p ON p.empresa_id = cc.empresa_id
            WHERE cc.empresa_id = :eid
              AND cc.customer_id = :cid
              AND p.deleted_at IS NULL
              AND (
                  LOWER(mc.content) LIKE '%' || LOWER(p.name) || '%'
                  OR LOWER(mc.content) LIKE '%' || LOWER(p.category) || '%'
              )
        """)
        result = await self._session.execute(
            raw, {"eid": empresa_id, "cid": customer_id}
        )
        return int(result.scalar_one_or_none() or 0)
