import { apiGet } from "@/services/api-client";
import type {
  InventoryAggregateMetrics,
  InventoryListResponse,
  InventoryProductDetail,
  InventorySortBy,
  InventoryStatusFilter,
} from "@/types/inventory";

type ListInventoryParams = {
  accessToken: string;
  search?: string;
  category?: string;
  status?: InventoryStatusFilter;
  sortBy?: InventorySortBy;
  sortDir?: "asc" | "desc";
  limit?: number;
  offset?: number;
};

function buildInventoryQuery(params: ListInventoryParams): string {
  const query = new URLSearchParams();
  query.set("limit", String(params.limit ?? 25));
  query.set("offset", String(params.offset ?? 0));
  if (params.search) query.set("search", params.search);
  if (params.category) query.set("category", params.category);
  if (params.status && params.status !== "all") query.set("status", params.status);
  if (params.sortBy) query.set("sort_by", params.sortBy);
  if (params.sortDir) query.set("sort_dir", params.sortDir);
  return query.toString();
}

export function listInventory(params: ListInventoryParams): Promise<InventoryListResponse> {
  return apiGet<InventoryListResponse>(`/inventory?${buildInventoryQuery(params)}`, {
    accessToken: params.accessToken,
  });
}

export function getInventoryMetrics(accessToken: string): Promise<InventoryAggregateMetrics> {
  return apiGet<InventoryAggregateMetrics>("/inventory/metrics", { accessToken });
}

export function getInventoryProduct(
  accessToken: string,
  productId: string,
): Promise<InventoryProductDetail> {
  return apiGet<InventoryProductDetail>(`/inventory/${productId}`, { accessToken });
}
