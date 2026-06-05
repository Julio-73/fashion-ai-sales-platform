import { apiGet } from "@/services/api-client";
import type { ExecutiveDashboardResponse } from "@/types/executive-dashboard";

export function getExecutiveDashboard(accessToken: string): Promise<ExecutiveDashboardResponse> {
  return apiGet<ExecutiveDashboardResponse>("/executive-dashboard/", { accessToken });
}
