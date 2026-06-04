import type {
  AdminAuditEntry,
  AdminAuthSession,
  AdminLoginPayload,
  AdminLogoutPayload,
  AdminRefreshPayload,
  AdminTokenResponse,
  AdminUser,
  EmpresaStatusUpdate,
  EmpresaTenant,
  EmpresaTenantCreate,
  EmpresaTenantUpdate,
  GlobalDashboard,
  Paginated
} from "@/types/admin";
import { apiGet, apiPatch, apiPost } from "@/services/api-client";

const ADMIN_PATH = "/admin";

export function adminLogin(payload: AdminLoginPayload): Promise<AdminAuthSession> {
  return apiPost<AdminAuthSession, AdminLoginPayload>(`${ADMIN_PATH}/auth/login`, payload);
}

export function adminRefresh(payload: AdminRefreshPayload): Promise<AdminTokenResponse> {
  return apiPost<AdminTokenResponse, AdminRefreshPayload>(
    `${ADMIN_PATH}/auth/refresh`,
    payload
  );
}

export function adminLogout(payload: AdminLogoutPayload): Promise<void> {
  return apiPost<void, AdminLogoutPayload>(`${ADMIN_PATH}/auth/logout`, payload);
}

export function adminMe(accessToken: string): Promise<AdminUser> {
  return apiGet<AdminUser>(`${ADMIN_PATH}/auth/me`, { accessToken });
}

export function adminDashboard(accessToken: string): Promise<GlobalDashboard> {
  return apiGet<GlobalDashboard>(`${ADMIN_PATH}/dashboard`, { accessToken });
}

export function adminListTenants(
  accessToken: string,
  params: { limit?: number; offset?: number; search?: string; status?: string; plan?: string } = {}
): Promise<Paginated<EmpresaTenant>> {
  const search = new URLSearchParams();
  if (params.limit !== undefined) search.set("limit", String(params.limit));
  if (params.offset !== undefined) search.set("offset", String(params.offset));
  if (params.search) search.set("search", params.search);
  if (params.status) search.set("status", params.status);
  if (params.plan) search.set("plan", params.plan);
  const qs = search.toString();
  const path = qs ? `${ADMIN_PATH}/tenants?${qs}` : `${ADMIN_PATH}/tenants`;
  return apiGet<Paginated<EmpresaTenant>>(path, { accessToken });
}

export function adminGetTenant(accessToken: string, tenantId: string): Promise<EmpresaTenant> {
  return apiGet<EmpresaTenant>(`${ADMIN_PATH}/tenants/${tenantId}`, { accessToken });
}

export function adminCreateTenant(
  accessToken: string,
  payload: EmpresaTenantCreate
): Promise<EmpresaTenant> {
  return apiPost<EmpresaTenant, EmpresaTenantCreate>(
    `${ADMIN_PATH}/tenants`,
    payload,
    { accessToken }
  );
}

export function adminUpdateTenant(
  accessToken: string,
  tenantId: string,
  payload: EmpresaTenantUpdate
): Promise<EmpresaTenant> {
  return apiPatch<EmpresaTenant, EmpresaTenantUpdate>(
    `${ADMIN_PATH}/tenants/${tenantId}`,
    payload,
    { accessToken }
  );
}

export function adminUpdateTenantStatus(
  accessToken: string,
  tenantId: string,
  payload: EmpresaStatusUpdate
): Promise<EmpresaTenant> {
  return apiPatch<EmpresaTenant, EmpresaStatusUpdate>(
    `${ADMIN_PATH}/tenants/${tenantId}/status`,
    payload,
    { accessToken }
  );
}

export function adminListAudit(
  accessToken: string,
  params: { limit?: number; offset?: number; action?: string; admin_user_id?: string; target_empresa_id?: string } = {}
): Promise<Paginated<AdminAuditEntry>> {
  const search = new URLSearchParams();
  if (params.limit !== undefined) search.set("limit", String(params.limit));
  if (params.offset !== undefined) search.set("offset", String(params.offset));
  if (params.action) search.set("action", params.action);
  if (params.admin_user_id) search.set("admin_user_id", params.admin_user_id);
  if (params.target_empresa_id) search.set("target_empresa_id", params.target_empresa_id);
  const qs = search.toString();
  const path = qs ? `${ADMIN_PATH}/audit?${qs}` : `${ADMIN_PATH}/audit`;
  return apiGet<Paginated<AdminAuditEntry>>(path, { accessToken });
}
