from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ProductVariantDTO(BaseModel):
    id: UUID
    product_id: UUID
    empresa_id: UUID
    talla: str | None
    color: str | None
    sku: str
    stock: int
    reserved_stock: int
    variant_price: Decimal | None
    created_at: datetime
    updated_at: datetime

    @property
    def available_stock(self) -> int:
        return self.stock - self.reserved_stock

    model_config = ConfigDict(from_attributes=True)


class ProductImageDTO(BaseModel):
    id: UUID
    product_id: UUID
    empresa_id: UUID
    image_url: str
    order_index: int

    model_config = ConfigDict(from_attributes=True)


class ProductDTO(BaseModel):
    id: UUID
    empresa_id: UUID
    name: str
    slug: str
    description: str | None
    category: str | None
    base_price: Decimal | None
    status: str
    variants: list[ProductVariantDTO] = []
    images: list[ProductImageDTO] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
