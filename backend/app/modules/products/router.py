from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.core.security.dependencies import TenantContext
from app.core.security.permissions import require_permission
from app.modules.products.dependencies import get_product_service
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
from app.modules.products.service import ProductService

router = APIRouter()


@router.get("", response_model=ProductListResponse)
async def list_products(
    tenant: Annotated[TenantContext, Depends(require_permission("products:read"))],
    service: Annotated[ProductService, Depends(get_product_service)],
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
    offset: Annotated[int, Query(ge=0)] = 0,
    search: Annotated[str | None, Query(min_length=1, max_length=120)] = None,
    category: Annotated[str | None, Query(max_length=80)] = None,
    status: Annotated[str | None, Query(max_length=32)] = None,
) -> ProductListResponse:
    return await service.list_products(
        tenant=tenant,
        limit=limit,
        offset=offset,
        search=search,
        category=category,
        status=status,
    )


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    payload: ProductCreateRequest,
    tenant: Annotated[TenantContext, Depends(require_permission("products:write"))],
    service: Annotated[ProductService, Depends(get_product_service)],
) -> ProductResponse:
    return await service.create_product(tenant=tenant, payload=payload)


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: UUID,
    tenant: Annotated[TenantContext, Depends(require_permission("products:read"))],
    service: Annotated[ProductService, Depends(get_product_service)],
) -> ProductResponse:
    return await service.get_product(tenant=tenant, product_id=product_id)


@router.patch("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: UUID,
    payload: ProductUpdateRequest,
    tenant: Annotated[TenantContext, Depends(require_permission("products:write"))],
    service: Annotated[ProductService, Depends(get_product_service)],
) -> ProductResponse:
    return await service.update_product(tenant=tenant, product_id=product_id, payload=payload)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: UUID,
    tenant: Annotated[TenantContext, Depends(require_permission("products:write"))],
    service: Annotated[ProductService, Depends(get_product_service)],
) -> None:
    await service.delete_product(tenant=tenant, product_id=product_id)


@router.post("/{product_id}/variants", response_model=ProductVariantResponse, status_code=status.HTTP_201_CREATED)
async def create_variant(
    product_id: UUID,
    payload: ProductVariantCreateRequest,
    tenant: Annotated[TenantContext, Depends(require_permission("products:write"))],
    service: Annotated[ProductService, Depends(get_product_service)],
) -> ProductVariantResponse:
    return await service.add_variant(tenant=tenant, product_id=product_id, payload=payload)


@router.patch("/{product_id}/variants/{variant_id}", response_model=ProductVariantResponse)
async def update_variant(
    product_id: UUID,
    variant_id: UUID,
    payload: ProductVariantUpdateRequest,
    tenant: Annotated[TenantContext, Depends(require_permission("products:write"))],
    service: Annotated[ProductService, Depends(get_product_service)],
) -> ProductVariantResponse:
    return await service.update_variant(tenant=tenant, product_id=product_id, variant_id=variant_id, payload=payload)


@router.delete("/{product_id}/variants/{variant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_variant(
    product_id: UUID,
    variant_id: UUID,
    tenant: Annotated[TenantContext, Depends(require_permission("products:write"))],
    service: Annotated[ProductService, Depends(get_product_service)],
) -> None:
    await service.delete_variant(tenant=tenant, product_id=product_id, variant_id=variant_id)


@router.post("/{product_id}/images", status_code=status.HTTP_201_CREATED)
async def add_image(
    product_id: UUID,
    payload: ProductImageCreateRequest,
    tenant: Annotated[TenantContext, Depends(require_permission("products:write"))],
    service: Annotated[ProductService, Depends(get_product_service)],
) -> dict:
    image = await service.add_image(tenant=tenant, product_id=product_id, payload=payload)
    return image.model_dump()


@router.delete("/{product_id}/images/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_image(
    product_id: UUID,
    image_id: UUID,
    tenant: Annotated[TenantContext, Depends(require_permission("products:write"))],
    service: Annotated[ProductService, Depends(get_product_service)],
) -> None:
    await service.delete_image(tenant=tenant, product_id=product_id, image_id=image_id)
