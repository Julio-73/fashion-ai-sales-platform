import { apiGet } from "@/services/api-client";
import type {
  CrmSortBy,
  CrmStatusFilter,
  Customer360ListResponse,
  Customer360Summary,
  CustomerAggregateMetrics,
  CustomerOrderHistoryResponse,
} from "@/types/crm";

type ListCustomer360Params = {
  accessToken: string;
  search?: string;
  status?: CrmStatusFilter;
  isVip?: boolean;
  isRecurrent?: boolean;
  dateFrom?: string;
  dateTo?: string;
  sortBy?: CrmSortBy;
  sortDir?: "asc" | "desc";
  limit?: number;
  offset?: number;
};

function buildListQuery(params: ListCustomer360Params): string {
  const q = new URLSearchParams();
  q.set("limit", String(params.limit ?? 25));
  q.set("offset", String(params.offset ?? 0));
  if (params.search) q.set("search", params.search);
  if (params.status && params.status !== "all") q.set("status", params.status);
  if (params.isVip) q.set("is_vip", "true");
  if (params.isRecurrent) q.set("is_recurrent", "true");
  if (params.dateFrom) q.set("date_from", params.dateFrom);
  if (params.dateTo) q.set("date_to", params.dateTo);
  if (params.sortBy) q.set("sort_by", params.sortBy);
  if (params.sortDir) q.set("sort_dir", params.sortDir);
  return q.toString();
}

export function listCustomer360(
  params: ListCustomer360Params
): Promise<Customer360ListResponse> {
  return apiGet<Customer360ListResponse>(
    `/crm/customers?${buildListQuery(params)}`,
    { accessToken: params.accessToken }
  );
}

export function getCustomerMetrics(
  accessToken: string
): Promise<CustomerAggregateMetrics> {
  return apiGet<CustomerAggregateMetrics>("/crm/metrics", { accessToken });
}

export function getCustomer360(
  accessToken: string,
  customerId: string
): Promise<Customer360Summary> {
  return apiGet<Customer360Summary>(`/crm/customers/${customerId}`, {
    accessToken,
  });
}

export function getCustomerOrders(
  accessToken: string,
  customerId: string,
  limit = 25,
  offset = 0
): Promise<CustomerOrderHistoryResponse> {
  const q = new URLSearchParams();
  q.set("limit", String(limit));
  q.set("offset", String(offset));
  return apiGet<CustomerOrderHistoryResponse>(
    `/crm/customers/${customerId}/orders?${q.toString()}`,
    { accessToken }
  );
}
