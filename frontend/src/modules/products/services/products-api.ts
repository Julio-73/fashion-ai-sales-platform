import { apiDelete, apiGet, apiPatch, apiPost } from "@/services/api-client";
import type {
  ProductCreatePayload,
  ProductImage,
  ProductImageCreatePayload,
  ProductListResponse,
  ProductSummary,
  ProductUpdatePayload,
  ProductVariant,
  ProductVariantCreatePayload,
  ProductVariantUpdatePayload
} from "@/types/product";

type ListProductsParams = {
  accessToken: string;
  search?: string;
  category?: string;
  status?: string;
  limit?: number;
  offset?: number;
};

function buildProductQuery(params: ListProductsParams) {
  const query = new URLSearchParams();
  query.set("limit", String(params.limit ?? 25));
  query.set("offset", String(params.offset ?? 0));
  if (params.search) query.set("search", params.search);
  if (params.category) query.set("category", params.category);
  if (params.status) query.set("status", params.status);
  return query.toString();
}

export function listProducts(params: ListProductsParams): Promise<ProductListResponse> {
  return apiGet<ProductListResponse>(`/products?${buildProductQuery(params)}`, {
    accessToken: params.accessToken
  });
}

export function createProduct(
  accessToken: string,
  payload: ProductCreatePayload
): Promise<ProductSummary> {
  return apiPost<ProductSummary, ProductCreatePayload>("/products", payload, { accessToken });
}

export function getProduct(
  accessToken: string,
  productId: string
): Promise<ProductSummary> {
  return apiGet<ProductSummary>(`/products/${productId}`, { accessToken });
}

export function updateProduct(
  accessToken: string,
  productId: string,
  payload: ProductUpdatePayload
): Promise<ProductSummary> {
  return apiPatch<ProductSummary, ProductUpdatePayload>(`/products/${productId}`, payload, { accessToken });
}

export function deleteProduct(accessToken: string, productId: string): Promise<void> {
  return apiDelete(`/products/${productId}`, { accessToken });
}

export function createVariant(
  accessToken: string,
  productId: string,
  payload: ProductVariantCreatePayload
): Promise<ProductVariant> {
  return apiPost<ProductVariant, ProductVariantCreatePayload>(`/products/${productId}/variants`, payload, { accessToken });
}

export function updateVariant(
  accessToken: string,
  productId: string,
  variantId: string,
  payload: ProductVariantUpdatePayload
): Promise<ProductVariant> {
  return apiPatch<ProductVariant, ProductVariantUpdatePayload>(`/products/${productId}/variants/${variantId}`, payload, { accessToken });
}

export function deleteVariant(
  accessToken: string,
  productId: string,
  variantId: string
): Promise<void> {
  return apiDelete(`/products/${productId}/variants/${variantId}`, { accessToken });
}

export function addProductImage(
  accessToken: string,
  productId: string,
  payload: ProductImageCreatePayload
): Promise<ProductImage> {
  return apiPost<ProductImage, ProductImageCreatePayload>(`/products/${productId}/images`, payload, { accessToken });
}

export function deleteProductImage(
  accessToken: string,
  productId: string,
  imageId: string
): Promise<void> {
  return apiDelete(`/products/${productId}/images/${imageId}`, { accessToken });
}
