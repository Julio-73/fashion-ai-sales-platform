"""Tests for ProductService."""
from __future__ import annotations
from unittest.mock import AsyncMock
from uuid import uuid4
from datetime import datetime, timezone
import pytest
from sqlalchemy.exc import IntegrityError
from app.core.errors import AppError
from app.modules.products.models import Producto, ProductVariant, ProductImage
from app.modules.products.schemas import (
    ProductCreateRequest, ProductUpdateRequest,
    ProductVariantCreateRequest, ProductVariantUpdateRequest,
    ProductImageCreateRequest,
)
from tests.conftest import TEST_PRODUCT_ID, TEST_VARIANT_ID, TEST_IMAGE_ID

pytestmark = pytest.mark.asyncio
_now = datetime.now(timezone.utc)


def _make_product(**kw):
    defaults = dict(id=uuid4(), empresa_id=TEST_PRODUCT_ID, name="Test", slug="test",
                    description=None, category=None, base_price=None, status="draft",
                    variants=[], images=[], created_at=_now, updated_at=_now, deleted_at=None)
    defaults.update(kw)
    return Producto(**defaults)


def _make_variant(**kw):
    defaults = dict(id=uuid4(), empresa_id=TEST_PRODUCT_ID, product_id=TEST_PRODUCT_ID,
                    talla=None, color=None, sku="SKU", stock=10, reserved_stock=0,
                    variant_price=None, created_at=_now, updated_at=_now, deleted_at=None)
    defaults.update(kw)
    return ProductVariant(**defaults)


class TestCreateProduct:
    async def test_creates_product_with_slug(self, product_service, product_repository, tenant_context):
        payload = ProductCreateRequest(name="  Vestido Floral Verano  ", category="vestidos", base_price=89.90)
        mock_p = _make_product(name="Vestido Floral Verano", slug="vestido-floral-verano",
                               category="vestidos", base_price=89.90, empresa_id=tenant_context.empresa_id)
        product_repository.create = AsyncMock(return_value=mock_p)
        product_repository.commit = AsyncMock()
        result = await product_service.create_product(tenant=tenant_context, payload=payload)
        assert result.name == "Vestido Floral Verano"
        assert product_repository.create.call_args.kwargs["slug"] == "vestido-floral-verano"

    async def test_empty_name_raises_422(self, product_service, tenant_context):
        with pytest.raises(AppError) as e:
            await product_service.create_product(tenant=tenant_context, payload=ProductCreateRequest(name="  "))
        assert e.value.status_code == 422

    async def test_duplicate_slug_raises_409(self, product_service, product_repository, tenant_context):
        product_repository.create = AsyncMock(side_effect=IntegrityError("mock", None, None))
        product_repository.rollback = AsyncMock()
        with pytest.raises(AppError) as e:
            await product_service.create_product(tenant=tenant_context, payload=ProductCreateRequest(name="Test"))
        assert e.value.status_code == 409


class TestGetProduct:
    async def test_returns_product(self, product_service, product_repository, tenant_context):
        mock_p = _make_product(id=TEST_PRODUCT_ID, empresa_id=tenant_context.empresa_id)
        product_repository.get_by_id = AsyncMock(return_value=mock_p)
        result = await product_service.get_product(tenant=tenant_context, product_id=TEST_PRODUCT_ID)
        assert result.id == TEST_PRODUCT_ID

    async def test_not_found_raises_404(self, product_service, product_repository, tenant_context):
        product_repository.get_by_id = AsyncMock(return_value=None)
        with pytest.raises(AppError) as e:
            await product_service.get_product(tenant=tenant_context, product_id=uuid4())
        assert e.value.status_code == 404


class TestUpdateProduct:
    async def test_updates_name_and_regenerates_slug(self, product_service, product_repository, tenant_context):
        mock_p = _make_product(id=TEST_PRODUCT_ID, empresa_id=tenant_context.empresa_id)
        product_repository.get_by_id = AsyncMock(return_value=mock_p)
        product_repository.update = AsyncMock(return_value=mock_p)
        product_repository.commit = AsyncMock()
        await product_service.update_product(tenant=tenant_context, product_id=TEST_PRODUCT_ID,
                                             payload=ProductUpdateRequest(name="  Nuevo  "))
        assert product_repository.update.call_args.kwargs["payload"]["slug"] == "nuevo"


class TestDeleteProduct:
    async def test_soft_deletes(self, product_service, product_repository, tenant_context):
        mock_p = _make_product(empresa_id=tenant_context.empresa_id)
        product_repository.get_by_id = AsyncMock(return_value=mock_p)
        product_repository.soft_delete = AsyncMock()
        product_repository.commit = AsyncMock()
        await product_service.delete_product(tenant=tenant_context, product_id=TEST_PRODUCT_ID)
        product_repository.soft_delete.assert_awaited_once()


class TestAddVariant:
    async def test_adds_variant(self, product_service, product_repository, tenant_context):
        mock_p = _make_product(id=TEST_PRODUCT_ID, empresa_id=tenant_context.empresa_id)
        mock_v = _make_variant(sku="VES-S", talla="S", color="Rojo", stock=10, variant_price=89.90)
        product_repository.get_by_id = AsyncMock(return_value=mock_p)
        product_repository.add_variant = AsyncMock(return_value=mock_v)
        product_repository.commit = AsyncMock()
        result = await product_service.add_variant(tenant=tenant_context, product_id=TEST_PRODUCT_ID,
                                                   payload=ProductVariantCreateRequest(sku="VES-S", stock=10, talla="S"))
        assert result.sku == "VES-S"


class TestUpdateVariant:
    async def test_updates_variant(self, product_service, product_repository, tenant_context):
        mock_p = _make_product(empresa_id=tenant_context.empresa_id)
        mock_v = _make_variant(stock=10, reserved_stock=2, empresa_id=tenant_context.empresa_id)
        product_repository.get_by_id = AsyncMock(return_value=mock_p)
        product_repository.get_variant_by_id = AsyncMock(return_value=mock_v)
        product_repository.update_variant = AsyncMock(return_value=mock_v)
        product_repository.commit = AsyncMock()
        await product_service.update_variant(tenant=tenant_context, product_id=TEST_PRODUCT_ID,
                                             variant_id=TEST_VARIANT_ID, payload=ProductVariantUpdateRequest(stock=20))
        assert product_repository.update_variant.call_args.kwargs["payload"]["stock"] == 20

    async def test_reserved_exceeds_stock_raises_422(self, product_service, product_repository, tenant_context):
        mock_p = _make_product(empresa_id=tenant_context.empresa_id)
        mock_v = _make_variant(stock=5, reserved_stock=0, empresa_id=tenant_context.empresa_id)
        product_repository.get_by_id = AsyncMock(return_value=mock_p)
        product_repository.get_variant_by_id = AsyncMock(return_value=mock_v)
        with pytest.raises(AppError) as e:
            await product_service.update_variant(tenant=tenant_context, product_id=TEST_PRODUCT_ID,
                                                 variant_id=TEST_VARIANT_ID,
                                                 payload=ProductVariantUpdateRequest(reserved_stock=10))
        assert e.value.status_code == 422
        assert e.value.code == "invalid_stock"


class TestDeleteVariant:
    async def test_soft_deletes_variant(self, product_service, product_repository, tenant_context):
        mock_p = _make_product(empresa_id=tenant_context.empresa_id)
        mock_v = _make_variant(empresa_id=tenant_context.empresa_id)
        product_repository.get_by_id = AsyncMock(return_value=mock_p)
        product_repository.get_variant_by_id = AsyncMock(return_value=mock_v)
        product_repository.soft_delete_variant = AsyncMock()
        product_repository.commit = AsyncMock()
        await product_service.delete_variant(tenant=tenant_context, product_id=TEST_PRODUCT_ID, variant_id=TEST_VARIANT_ID)
        product_repository.soft_delete_variant.assert_awaited_once()


class TestAddImage:
    async def test_adds_image(self, product_service, product_repository, tenant_context):
        from app.modules.products.dtos import ProductImageDTO
        mock_p = _make_product(empresa_id=tenant_context.empresa_id)
        product_repository.get_by_id = AsyncMock(return_value=mock_p)
        product_repository.add_image = AsyncMock()
        product_repository.commit = AsyncMock()
        # Mock the add_image to return a ProductImageDTO directly since the service returns ProductImageDTO
        expected = ProductImageDTO(id=uuid4(), product_id=TEST_PRODUCT_ID, empresa_id=tenant_context.empresa_id,
                                   image_url="https://example.com/img.jpg", order_index=0)
        product_repository.add_image = AsyncMock(return_value=expected)
        result = await product_service.add_image(tenant=tenant_context, product_id=TEST_PRODUCT_ID,
                                                 payload=ProductImageCreateRequest(image_url="https://example.com/img.jpg"))
        assert result.image_url == "https://example.com/img.jpg"
