import logging
from uuid import UUID

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.modules.products.models import Producto, ProductVariant
from app.smart_sales.entity_extractor import ExtractedEntities, PRODUCT_ALIASES, COLOR_ALIASES
from app.smart_sales.product_matcher import MatchedProduct, MatchedVariant, ProductMatcher

logger = logging.getLogger("ai_sales_agent.smart_sales.product_context")


class ProductContextEngine:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._matcher = ProductMatcher()

    async def find_products(
        self,
        *,
        empresa_id: UUID,
        entities: ExtractedEntities,
        limit: int = 10,
    ) -> list[MatchedProduct]:
        products = await self._query_products(empresa_id, entities, limit)
        scored = self._score_and_match(products, entities)
        scored.sort(key=lambda p: p.score, reverse=True)
        return scored[:limit]

    async def get_related_products(
        self,
        *,
        empresa_id: UUID,
        product_category: str | None = None,
        exclude_product_id: UUID | None = None,
        limit: int = 3,
    ) -> list[MatchedProduct]:
        stmt = (
            select(Producto)
            .options(joinedload(Producto.variants))
            .where(
                Producto.empresa_id == empresa_id,
                Producto.deleted_at.is_(None),
                Producto.status == "active",
            )
        )
        if product_category:
            stmt = stmt.where(Producto.category == product_category)
        if exclude_product_id:
            stmt = stmt.where(Producto.id != exclude_product_id)
        stmt = stmt.limit(limit * 2)
        result = await self._session.execute(stmt)
        products = result.unique().scalars().all()
        return [self._to_matched(p, 0.0, "relacionado") for p in products[:limit]]

    async def _query_products(
        self,
        empresa_id: UUID,
        entities: ExtractedEntities,
        limit: int,
    ) -> list[Producto]:
        stmt = (
            select(Producto)
            .options(joinedload(Producto.variants))
            .where(
                Producto.empresa_id == empresa_id,
                Producto.deleted_at.is_(None),
                Producto.status == "active",
            )
        )

        if entities.product_type:
            category_aliases = PRODUCT_ALIASES.get(entities.product_type, [entities.product_type])
            category_filters = [
                Producto.category.ilike(f"%{alias}%")
                for alias in category_aliases
            ]
            name_filters = [
                Producto.name.ilike(f"%{alias}%")
                for alias in category_aliases
            ]
            stmt = stmt.where(or_(*category_filters, *name_filters))

        if entities.color:
            color_aliases = [c for c, v in COLOR_ALIASES.items() if v == entities.color]
            color_filters = [
                ProductVariant.color.ilike(f"%{alias}%")
                for alias in color_aliases
            ]
            stmt = stmt.join(Producto.variants).where(or_(*color_filters))

        stmt = stmt.limit(limit * 3)
        result = await self._session.execute(stmt)
        return result.unique().scalars().all()

    def _score_and_match(
        self,
        products: list[Producto],
        entities: ExtractedEntities,
    ) -> list[MatchedProduct]:
        matched = []
        for product in products:
            score = self._matcher.score_product(
                product_name=product.name,
                product_category=product.category,
                entities=entities,
            )
            if entities.size:
                size_match = any(
                    v.talla and v.talla.upper() == entities.size.upper()
                    for v in product.variants
                )
                if size_match:
                    score += 25.0
                else:
                    score -= 10.0
            mp = self._to_matched(product, score, "scored")
            matched.append(mp)
        return matched

    def _to_matched(self, product: Producto, score: float, reason: str) -> MatchedProduct:
        variants = [
            MatchedVariant(
                variant_id=str(v.id),
                talla=v.talla,
                color=v.color,
                price=float(v.variant_price) if v.variant_price else float(product.base_price) if product.base_price else None,
                stock=v.stock,
                reserved_stock=v.reserved_stock,
                sku=v.sku,
            )
            for v in product.variants
            if v.deleted_at is None
        ]
        return MatchedProduct(
            product_id=str(product.id),
            name=product.name,
            category=product.category,
            base_price=float(product.base_price) if product.base_price else None,
            available_variants=variants,
            score=score,
            match_reason=reason,
        )
