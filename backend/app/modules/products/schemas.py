from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

ProductStatus = Literal["active", "inactive", "draft"]


class ProductVariantResponse(BaseModel):
    id: UUID
    product_id: UUID
    empresa_id: UUID
    talla: str | None
    color: str | None
    sku: str
    stock: int
    reserved_stock: int
    available_stock: int
    variant_price: Decimal | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProductImageResponse(BaseModel):
    id: UUID
    product_id: UUID
    empresa_id: UUID
    image_url: str
    order_index: int

    model_config = ConfigDict(from_attributes=True)


class ProductResponse(BaseModel):
    id: UUID
    empresa_id: UUID
    name: str
    slug: str
    description: str | None
    category: str | None
    base_price: Decimal | None
    status: ProductStatus
    variants: list[ProductVariantResponse] = []
    images: list[ProductImageResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProductListResponse(BaseModel):
    items: list[ProductResponse]
    total: int
    limit: int
    offset: int


class ProductCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=180)
    description: str | None = Field(default=None, max_length=4000)
    category: str | None = Field(default=None, max_length=80)
    base_price: Decimal | None = Field(default=None, ge=0)
    status: ProductStatus = "draft"


class ProductUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=180)
    description: str | None = Field(default=None, max_length=4000)
    category: str | None = Field(default=None, max_length=80)
    base_price: Decimal | None = Field(default=None, ge=0)
    status: ProductStatus | None = None


class ProductVariantCreateRequest(BaseModel):
    talla: str | None = Field(default=None, max_length=32)
    color: str | None = Field(default=None, max_length=48)
    sku: str = Field(min_length=1, max_length=80)
    stock: int = Field(default=0, ge=0)
    variant_price: Decimal | None = Field(default=None, ge=0)


class ProductVariantUpdateRequest(BaseModel):
    talla: str | None = Field(default=None, max_length=32)
    color: str | None = Field(default=None, max_length=48)
    sku: str | None = Field(default=None, min_length=1, max_length=80)
    stock: int | None = Field(default=None, ge=0)
    reserved_stock: int | None = Field(default=None, ge=0)
    variant_price: Decimal | None = Field(default=None, ge=0)


class ProductImageCreateRequest(BaseModel):
    image_url: str = Field(min_length=1, max_length=1024)
    order_index: int = Field(default=0, ge=0)
