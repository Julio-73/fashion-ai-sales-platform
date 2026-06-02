export type CustomerLifecycleStatus =
  | "nuevo"
  | "activo"
  | "recurrente"
  | "vip"
  | "inactivo";

export type CrmSortBy =
  | "created_at"
  | "full_name"
  | "lifetime_value"
  | "last_purchase_at"
  | "order_count";

export type CrmStatusFilter =
  | "all"
  | "nuevo"
  | "activo"
  | "recurrente"
  | "vip"
  | "inactivo";

export type CustomerMetrics = {
  order_count: number;
  lifetime_value: string;
  average_ticket: string;
  first_purchase_at: string | null;
  last_purchase_at: string | null;
  days_since_last_purchase: number | null;
  status: CustomerLifecycleStatus;
};

export type Customer360Summary = {
  id: string;
  empresa_id: string;
  full_name: string;
  email: string | null;
  phone: string | null;
  whatsapp: string | null;
  instagram_username: string | null;
  tags: string[];
  notes: string | null;
  lead_status: string;
  source: string | null;
  assigned_to: string | null;
  created_at: string;
  updated_at: string;
  metrics: CustomerMetrics;
};

export type CustomerAggregateMetrics = {
  total_customers: number;
  new_customers: number;
  active_customers: number;
  recurrent_customers: number;
  vip_customers: number;
  inactive_customers: number;
  total_lifetime_value: string;
  average_ticket: string;
  average_orders_per_customer: string;
};

export type Customer360ListResponse = {
  items: Customer360Summary[];
  total: number;
  limit: number;
  offset: number;
  aggregate: CustomerAggregateMetrics;
};

export type CustomerOrderHistoryItem = {
  order_id: string;
  order_number: string;
  created_at: string;
  status: string;
  total: string;
  items_count: number;
  primary_product_name: string;
};

export type CustomerOrderHistoryResponse = {
  customer_id: string;
  total: number;
  limit: number;
  offset: number;
  items: CustomerOrderHistoryItem[];
};
