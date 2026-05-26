import { apiGet, apiPost } from "@/services/api-client";
import type {
  AnalyzeMessageResponse,
  CustomerSalesProfileResponse,
  SalesActivityResponse,
  SalesInsightsResponse,
  SalesRecommendationsResponse,
  TopLeadsResponse,
} from "@/types/sales";

export function getSalesInsights(accessToken: string): Promise<SalesInsightsResponse> {
  return apiGet<SalesInsightsResponse>("/sales/insights", { accessToken });
}

export function getTopLeads(accessToken: string, limit = 50): Promise<TopLeadsResponse> {
  return apiGet<TopLeadsResponse>(`/sales/top-leads?limit=${limit}`, { accessToken });
}

export function getRecommendations(accessToken: string): Promise<SalesRecommendationsResponse> {
  return apiGet<SalesRecommendationsResponse>("/sales/recommendations", { accessToken });
}

export function getCustomerSalesProfile(accessToken: string, customerId: string): Promise<CustomerSalesProfileResponse> {
  return apiGet<CustomerSalesProfileResponse>(`/sales/customers/${customerId}`, { accessToken });
}

export function getSalesActivity(accessToken: string, limit = 50): Promise<SalesActivityResponse> {
  return apiGet<SalesActivityResponse>(`/sales/activity?limit=${limit}`, { accessToken });
}

export function analyzeMessage(
  accessToken: string,
  customerId: string,
  message: string
): Promise<AnalyzeMessageResponse> {
  return apiPost<AnalyzeMessageResponse, { customer_id: string; message: string }>(
    "/sales/analyze-message",
    { customer_id: customerId, message },
    { accessToken }
  );
}
