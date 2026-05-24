from collections.abc import Sequence
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.products.models import ProductImage, ProductVariant, Producto
from app.modules.products.schemas import (
    ProductCreateRequest,
    ProductImageCreateRequest,
    ProductUpdateRequest,
    ProductVariantCreateRequest,
    ProductVariantUpdateRequest,
)


class ProductRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, *, empresa_id: UUID, slug: str, payload: ProductCreateRequest) -> Producto:
        product = Producto(empresa_id=empresa_id, slug=slug, **payload.model_dump())
        self._session.add(product)
        await self._session.flush()
        await self._session.refresh(product, attribute_names=["variants", "images"])
        return product

    async def get_by_id(self, *, empresa_id: UUID, product_id: UUID) -> Producto | None:
        result = await self._session.execute(
            select(Producto)
            .options(joinedload(Producto.variants), joinedload(Producto.images))
            .where(
                Producto.empresa_id == empresa_id,
                Producto.id == product_id,
                Producto.deleted_at.is_(None),
            )
        )
        return result.unique().scalar_one_or_none()

    async def list(
        self,
        *,
        empresa_id: UUID,
        limit: int,
        offset: int,
        search: str | None = None,
        category: str | None = None,
        status: str | None = None,
    ) -> tuple[Sequence[Producto], int]:
        query = self._filtered_query(empresa_id=empresa_id, search=search, category=category, status=status)
        count_result = await self._session.execute(select(func.count()).select_from(query.subquery()))
        total = int(count_result.scalar_one())

        result = await self._session.execute(
            query
            .options(joinedload(Producto.variants), joinedload(Producto.images))
            .order_by(Producto.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return result.unique().scalars().all(), total

    async def update(
        self,
        *,
        product: Producto,
        payload: ProductUpdateRequest | dict,
    ) -> Producto:
        values = payload.model_dump(exclude_unset=True) if not isinstance(payload, dict) else payload
        for field, value in values.items():
            setattr(product, field, value)
        await self._session.flush()
        await self._session.refresh(product, attribute_names=["variants", "images"])
        return product

    async def soft_delete(self, *, product: Producto) -> None:
        product.deleted_at = datetime.now(UTC)
        await self._session.flush()

    async def add_variant(
        self,
        *,
        empresa_id: UUID,
        product_id: UUID,
        payload: ProductVariantCreateRequest,
    ) -> ProductVariant:
        variant = ProductVariant(
            empresa_id=empresa_id,
            product_id=product_id,
            **payload.model_dump(),
        )
        self._session.add(variant)
        await self._session.flush()
        return variant

    async def get_variant_by_id(
        self,
        *,
        empresa_id: UUID,
        product_id: UUID,
        variant_id: UUID,
    ) -> ProductVariant | None:
        result = await self._session.execute(
            select(ProductVariant).where(
                ProductVariant.empresa_id == empresa_id,
                ProductVariant.product_id == product_id,
                ProductVariant.id == variant_id,
                ProductVariant.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def update_variant(
        self,
        *,
        variant: ProductVariant,
        payload: ProductVariantUpdateRequest | dict,
    ) -> ProductVariant:
        values = payload.model_dump(exclude_unset=True) if not isinstance(payload, dict) else payload
        for field, value in values.items():
            setattr(variant, field, value)
        await self._session.flush()
        return variant

    async def soft_delete_variant(self, *, variant: ProductVariant) -> None:
        variant.deleted_at = datetime.now(UTC)
        await self._session.flush()

    async def add_image(
        self,
        *,
        empresa_id: UUID,
        product_id: UUID,
        payload: ProductImageCreateRequest,
    ) -> ProductImage:
        image = ProductImage(
            empresa_id=empresa_id,
            product_id=product_id,
            image_url=payload.image_url,
            order_index=payload.order_index,
        )
        self._session.add(image)
        await self._session.flush()
        return image

    async def get_image_by_id(
        self,
        *,
        empresa_id: UUID,
        product_id: UUID,
        image_id: UUID,
    ) -> ProductImage | None:
        result = await self._session.execute(
            select(ProductImage).where(
                ProductImage.empresa_id == empresa_id,
                ProductImage.product_id == product_id,
                ProductImage.id == image_id,
            )
        )
        return result.scalar_one_or_none()

    async def delete_image(self, *, image: ProductImage) -> None:
        await self._session.delete(image)
        await self._session.flush()

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()

    def _filtered_query(
        self,
        *,
        empresa_id: UUID,
        search: str | None,
        category: str | None,
        status: str | None,
    ) -> Select[tuple[Producto]]:
        query = select(Producto).where(
            Producto.empresa_id == empresa_id,
            Producto.deleted_at.is_(None),
        )
        if category:
            query = query.where(Producto.category == category)
        if status:
            query = query.where(Producto.status == status)
        if search:
            pattern = f"%{search.strip()}%"
            query = query.where(
                or_(
                    Producto.name.ilike(pattern),
                    Producto.slug.ilike(pattern),
                    Producto.category.ilike(pattern),
                )
            )
        return query
