import { apiGet, apiPatch } from "@/services/api-client";
import type { OrderListResponse, OrderMetrics, OrderStatus, OrderSummary } from "@/types/order";

type ListOrdersParams = {
  accessToken: string;
  status?: OrderStatus | "all";
  customer?: string;
  dateFrom?: string;
  dateTo?: string;
  limit?: number;
  offset?: number;
};

function buildOrderQuery(params: ListOrdersParams) {
  const query = new URLSearchParams();
  query.set("limit", String(params.limit ?? 25));
  query.set("offset", String(params.offset ?? 0));
  if (params.status && params.status !== "all") query.set("status", params.status);
  if (params.customer) query.set("customer", params.customer);
  if (params.dateFrom) query.set("date_from", params.dateFrom);
  if (params.dateTo) query.set("date_to", params.dateTo);
  return query.toString();
}

export function listOrders(params: ListOrdersParams): Promise<OrderListResponse> {
  return apiGet<OrderListResponse>(`/orders?${buildOrderQuery(params)}`, {
    accessToken: params.accessToken,
  });
}

export function getOrderMetrics(accessToken: string): Promise<OrderMetrics> {
  return apiGet<OrderMetrics>("/orders/metrics", { accessToken });
}

export function updateOrderStatus(
  accessToken: string,
  orderId: string,
  status: OrderStatus,
): Promise<OrderSummary> {
  return apiPatch<OrderSummary, { status: OrderStatus }>(
    `/orders/${orderId}/status`,
    { status },
    { accessToken },
  );
}
