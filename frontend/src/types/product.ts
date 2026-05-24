export type ProductStatus = "active" | "inactive" | "draft";

export type ProductVariant = {
  id: string;
  product_id: string;
  empresa_id: string;
  talla: string | null;
  color: string | null;
  sku: string;
  stock: number;
  reserved_stock: number;
  available_stock: number;
  variant_price: string | null;
  created_at: string;
  updated_at: string;
};

export type ProductImage = {
  id: string;
  product_id: string;
  empresa_id: string;
  image_url: string;
  order_index: number;
};

export type ProductSummary = {
  id: string;
  empresa_id: string;
  name: string;
  slug: string;
  description: string | null;
  category: string | null;
  base_price: string | null;
  status: ProductStatus;
  variants: ProductVariant[];
  images: ProductImage[];
  created_at: string;
  updated_at: string;
};

export type ProductListResponse = {
  items: ProductSummary[];
  total: number;
  limit: number;
  offset: number;
};

export type ProductCreatePayload = {
  name: string;
  description?: string | null;
  category?: string | null;
  base_price?: string | null;
  status?: ProductStatus;
};

export type ProductUpdatePayload = Partial<ProductCreatePayload>;

export type ProductVariantCreatePayload = {
  talla?: string | null;
  color?: string | null;
  sku: string;
  stock?: number;
  variant_price?: string | null;
};

export type ProductVariantUpdatePayload = Partial<ProductVariantCreatePayload> & {
  reserved_stock?: number | null;
};

export type ProductImageCreatePayload = {
  image_url: string;
  order_index?: number;
};
