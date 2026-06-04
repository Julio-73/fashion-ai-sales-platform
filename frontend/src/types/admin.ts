export type AdminRole = "super_admin" | "company_admin" | "agent";

export type AdminUser = {
  id: string;
  email: string;
  full_name: string | null;
  rol: AdminRole;
  is_active: boolean;
  is_super_admin: boolean;
  permissions: string[];
  last_login_at: string | null;
  created_at: string;
};

export type AdminLoginPayload = {
  email: string;
  password: string;
};

export type AdminRefreshPayload = {
  refresh_token: string;
};

export type AdminLogoutPayload = {
  refresh_token: string;
};

export type AdminTokenResponse = {
  access_token: string;
  refresh_token: string;
  token_type: "bearer";
  expires_in: number;
};

export type AdminAuthSession = AdminTokenResponse & {
  user: AdminUser;
};

export type EmpresaPlan = "basic" | "pro" | "enterprise";
export type EmpresaStatus = "active" | "suspended" | "expired";

export type EmpresaTenant = {
  id: string;
  nombre: string;
  slug: string;
  plan: EmpresaPlan;
  status: EmpresaStatus;
  logo_url: string | null;
  created_at: string;
  updated_at: string;
};

export type EmpresaTenantCreate = {
  nombre: string;
  slug: string;
  plan: EmpresaPlan;
  status?: EmpresaStatus;
  logo_url?: string | null;
};

export type EmpresaTenantUpdate = {
  nombre?: string;
  plan?: EmpresaPlan;
  logo_url?: string | null;
  status?: EmpresaStatus;
};

export type EmpresaStatusUpdate = {
  status: EmpresaStatus;
};

export type Paginated<T> = {
  items: T[];
  total: number;
  limit: number;
  offset: number;
};

export type GlobalDashboard = {
  total_empresas: number;
  empresas_activas: number;
  empresas_suspendidas: number;
  empresas_expiradas: number;
  total_clientes: number;
  total_pedidos: number;
  total_conversaciones: number;
  total_ventas: number;
  planes_breakdown: Record<string, number>;
  status_breakdown: Record<string, number>;
};

export type AdminAuditEntry = {
  id: string;
  admin_user_id: string;
  admin_email: string | null;
  target_empresa_id: string | null;
  action: string;
  details: Record<string, unknown> | null;
  ip_address: string | null;
  created_at: string;
};
