import re
from uuid import UUID

from sqlalchemy.exc import IntegrityError

from app.core.errors import AppError
from app.core.security.dependencies import TenantContext
from app.modules.products.dtos import ProductDTO, ProductImageDTO, ProductVariantDTO
from app.modules.products.models import Producto
from app.modules.products.repository import ProductRepository
from app.modules.products.schemas import (
    ProductCreateRequest,
    ProductImageCreateRequest,
    ProductListResponse,
    ProductResponse,
    ProductUpdateRequest,
    ProductVariantCreateRequest,
    ProductVariantResponse,
    ProductVariantUpdateRequest,
)


def _slugify(name: str) -> str:
    slug = name.lower().strip()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"[\s-]+", "-", slug)
    return slug[:200].rstrip("-")


class ProductService:
    def __init__(self, repository: ProductRepository) -> None:
        self._repository = repository

    async def create_product(
        self,
        *,
        tenant: TenantContext,
        payload: ProductCreateRequest,
    ) -> ProductResponse:
        name = payload.name.strip()
        if not name:
            raise AppError(code="invalid_input", message="Product name cannot be empty", status_code=422)
        slug = _slugify(name)
        sanitized = payload.model_copy(update={"name": name})
        try:
            product = await self._repository.create(empresa_id=tenant.empresa_id, slug=slug, payload=sanitized)
            await self._repository.commit()
            return ProductResponse.model_validate(ProductDTO.model_validate(product))
        except IntegrityError as exc:
            await self._repository.rollback()
            raise AppError(code="product_conflict", message="A product with this slug already exists", status_code=409) from exc

    async def get_product(self, *, tenant: TenantContext, product_id: UUID) -> ProductResponse:
        product = await self._get_product_or_404(empresa_id=tenant.empresa_id, product_id=product_id)
        return ProductResponse.model_validate(ProductDTO.model_validate(product))

    async def list_products(
        self,
        *,
        tenant: TenantContext,
        limit: int,
        offset: int,
        search: str | None,
        category: str | None,
        status: str | None,
    ) -> ProductListResponse:
        products, total = await self._repository.list(
            empresa_id=tenant.empresa_id,
            limit=limit,
            offset=offset,
            search=search,
            category=category,
            status=status,
        )
        return ProductListResponse(
            items=[ProductResponse.model_validate(ProductDTO.model_validate(p)) for p in products],
            total=total,
            limit=limit,
            offset=offset,
        )

    async def update_product(
        self,
        *,
        tenant: TenantContext,
        product_id: UUID,
        payload: ProductUpdateRequest,
    ) -> ProductResponse:
        product = await self._get_product_or_404(empresa_id=tenant.empresa_id, product_id=product_id)
        dump = payload.model_dump(exclude_unset=True)
        if "name" in dump:
            name = dump["name"].strip()
            if not name:
                raise AppError(code="invalid_input", message="Product name cannot be empty", status_code=422)
            dump["name"] = name
            dump["slug"] = _slugify(name)
        try:
            updated = await self._repository.update(product=product, payload=dump)
            await self._repository.commit()
            return ProductResponse.model_validate(ProductDTO.model_validate(updated))
        except IntegrityError as exc:
            await self._repository.rollback()
            raise AppError(code="product_conflict", message="Product update conflicts with an existing product", status_code=409) from exc

    async def delete_product(self, *, tenant: TenantContext, product_id: UUID) -> None:
        product = await self._get_product_or_404(empresa_id=tenant.empresa_id, product_id=product_id)
        await self._repository.soft_delete(product=product)
        await self._repository.commit()

    async def add_variant(
        self,
        *,
        tenant: TenantContext,
        product_id: UUID,
        payload: ProductVariantCreateRequest,
    ) -> ProductVariantResponse:
        await self._get_product_or_404(empresa_id=tenant.empresa_id, product_id=product_id)
        try:
            variant = await self._repository.add_variant(
                empresa_id=tenant.empresa_id,
                product_id=product_id,
                payload=payload,
            )
            await self._repository.commit()
            return ProductVariantResponse.model_validate(ProductVariantDTO.model_validate(variant))
        except IntegrityError as exc:
            await self._repository.rollback()
            raise AppError(code="variant_conflict", message="A variant with this SKU already exists", status_code=409) from exc

    async def update_variant(
        self,
        *,
        tenant: TenantContext,
        product_id: UUID,
        variant_id: UUID,
        payload: ProductVariantUpdateRequest,
    ) -> ProductVariantResponse:
        await self._get_product_or_404(empresa_id=tenant.empresa_id, product_id=product_id)
        variant = await self._get_variant_or_404(
            empresa_id=tenant.empresa_id,
            product_id=product_id,
            variant_id=variant_id,
        )
        dump = payload.model_dump(exclude_unset=True)
        new_stock = dump.get("stock", variant.stock) if "stock" in dump else variant.stock
        new_reserved = dump.get("reserved_stock", variant.reserved_stock) if "reserved_stock" in dump else variant.reserved_stock
        if new_reserved > new_stock:
            raise AppError(
                code="invalid_stock",
                message="Reserved stock cannot exceed total stock",
                status_code=422,
            )
        try:
            updated = await self._repository.update_variant(variant=variant, payload=dump)
            await self._repository.commit()
            return ProductVariantResponse.model_validate(ProductVariantDTO.model_validate(updated))
        except IntegrityError as exc:
            await self._repository.rollback()
            raise AppError(code="variant_conflict", message="Variant update conflicts with an existing variant", status_code=409) from exc

    async def delete_variant(
        self,
        *,
        tenant: TenantContext,
        product_id: UUID,
        variant_id: UUID,
    ) -> None:
        await self._get_product_or_404(empresa_id=tenant.empresa_id, product_id=product_id)
        variant = await self._get_variant_or_404(
            empresa_id=tenant.empresa_id,
            product_id=product_id,
            variant_id=variant_id,
        )
        await self._repository.soft_delete_variant(variant=variant)
        await self._repository.commit()

    async def add_image(
        self,
        *,
        tenant: TenantContext,
        product_id: UUID,
        payload: ProductImageCreateRequest,
    ) -> ProductImageDTO:
        await self._get_product_or_404(empresa_id=tenant.empresa_id, product_id=product_id)
        image = await self._repository.add_image(
            empresa_id=tenant.empresa_id,
            product_id=product_id,
            payload=payload,
        )
        await self._repository.commit()
        return ProductImageDTO.model_validate(image)

    async def delete_image(
        self,
        *,
        tenant: TenantContext,
        product_id: UUID,
        image_id: UUID,
    ) -> None:
        await self._get_product_or_404(empresa_id=tenant.empresa_id, product_id=product_id)
        image = await self._get_image_or_404(
            empresa_id=tenant.empresa_id,
            product_id=product_id,
            image_id=image_id,
        )
        await self._repository.delete_image(image=image)
        await self._repository.commit()

    async def _get_product_or_404(self, *, empresa_id: UUID, product_id: UUID) -> Producto:
        product = await self._repository.get_by_id(empresa_id=empresa_id, product_id=product_id)
        if product is None:
            raise AppError(code="product_not_found", message="Product not found", status_code=404)
        return product

    async def _get_variant_or_404(self, *, empresa_id: UUID, product_id: UUID, variant_id: UUID):
        variant = await self._repository.get_variant_by_id(
            empresa_id=empresa_id,
            product_id=product_id,
            variant_id=variant_id,
        )
        if variant is None:
            raise AppError(code="variant_not_found", message="Variant not found", status_code=404)
        return variant

    async def _get_image_or_404(self, *, empresa_id: UUID, product_id: UUID, image_id: UUID):
        image = await self._repository.get_image_by_id(
            empresa_id=empresa_id,
            product_id=product_id,
            image_id=image_id,
        )
        if image is None:
            raise AppError(code="image_not_found", message="Image not found", status_code=404)
        return image
