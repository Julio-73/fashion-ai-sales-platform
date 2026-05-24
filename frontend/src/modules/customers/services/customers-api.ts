import { apiDelete, apiGet, apiPatch, apiPost } from "@/services/api-client";
import type {
  CustomerCreatePayload,
  CustomerListResponse,
  CustomerSummary,
  CustomerUpdatePayload,
  LeadStatus
} from "@/types/customer";

type ListCustomersParams = {
  accessToken: string;
  search?: string;
  leadStatus?: LeadStatus | "all";
  limit?: number;
  offset?: number;
};

function buildCustomerQuery(params: ListCustomersParams) {
  const query = new URLSearchParams();
  query.set("limit", String(params.limit ?? 25));
  query.set("offset", String(params.offset ?? 0));
  if (params.search) query.set("search", params.search);
  if (params.leadStatus && params.leadStatus !== "all") query.set("lead_status", params.leadStatus);
  return query.toString();
}

export function listCustomers(params: ListCustomersParams): Promise<CustomerListResponse> {
  return apiGet<CustomerListResponse>(`/customers?${buildCustomerQuery(params)}`, {
    accessToken: params.accessToken
  });
}

export function createCustomer(
  accessToken: string,
  payload: CustomerCreatePayload
): Promise<CustomerSummary> {
  return apiPost<CustomerSummary, CustomerCreatePayload>("/customers", payload, { accessToken });
}

export function updateCustomer(
  accessToken: string,
  customerId: string,
  payload: CustomerUpdatePayload
): Promise<CustomerSummary> {
  return apiPatch<CustomerSummary, CustomerUpdatePayload>(`/customers/${customerId}`, payload, { accessToken });
}

export function deleteCustomer(accessToken: string, customerId: string): Promise<void> {
  return apiDelete(`/customers/${customerId}`, { accessToken });
}
