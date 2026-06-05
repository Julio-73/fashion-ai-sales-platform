export type ExecutiveDashboardPeriod = {
  today: string;
  week_start: string;
  month_start: string;
  year_start: string;
};

export type ExecutiveDashboardKpis = {
  sales_today: number;
  sales_week: number;
  sales_month: number;
  sales_year: number;
  average_ticket: number;
  average_ticket_month: number;
  active_customers: number;
  vip_customers: number;
  active_conversations: number;
  leads_open: number;
  leads_won: number;
  leads_lost: number;
  conversion_rate_pct: number;
  total_orders: number;
};

export type ExecutiveDashboardDailyTrend = {
  date: string;
  revenue: number | string;
  orders: number;
};

export type ExecutiveDashboardMonthlyTrend = {
  month: string;
  revenue: number | string;
  orders: number;
};

export type ExecutiveDashboardSalesTrend = {
  daily: ExecutiveDashboardDailyTrend[];
  monthly: ExecutiveDashboardMonthlyTrend[];
};

export type ExecutiveDashboardFunnelStage = {
  stage: string;
  label: string;
  count: number;
  value: number;
  order: number;
  color: string;
};

export type ExecutiveDashboardPipeline = {
  total_value: number;
  weighted_value: number;
  won_value: number;
  lost_value: number;
  conversion_pct: number;
  average_time_to_close_days: number;
  open_deals: number;
  won_deals: number;
  lost_deals: number;
  funnel: ExecutiveDashboardFunnelStage[];
};

export type ExecutiveDashboardRecommendationPriority = "high" | "medium" | "low";

export type ExecutiveDashboardRecommendation = {
  id: string;
  title: string;
  description: string;
  score: number;
  priority: ExecutiveDashboardRecommendationPriority;
  category: string;
  cta_label: string;
  cta_href: string | null;
};

export type ExecutiveDashboardForecastConfidence = "low" | "medium" | "high";

export type ExecutiveDashboardForecastPeriod = {
  projected_revenue: number;
  confidence: ExecutiveDashboardForecastConfidence;
  basis: string;
  sample_size: number;
};

export type ExecutiveDashboardForecast = {
  monthly: ExecutiveDashboardForecastPeriod;
  quarterly: ExecutiveDashboardForecastPeriod;
};

export type ExecutiveDashboardTopCustomer = {
  id: string;
  full_name: string;
  email: string | null;
  phone: string | null;
  is_vip: boolean;
  order_count: number;
  lifetime_value: number;
  average_ticket: number;
  days_since_last_purchase: number | null;
};

export type ExecutiveDashboardTopProductSold = {
  product_id: string;
  name: string;
  units_sold: number;
  revenue: number;
};

export type ExecutiveDashboardTopProductProfitable = {
  product_id: string;
  name: string;
  revenue: number;
  units_sold: number;
};

export type ExecutiveDashboardTopProductConsulted = {
  product_id: string;
  name: string;
  mentions: number;
};

export type ExecutiveDashboardTopProducts = {
  most_sold: ExecutiveDashboardTopProductSold[];
  most_profitable: ExecutiveDashboardTopProductProfitable[];
  most_consulted: ExecutiveDashboardTopProductConsulted[];
};

export type ExecutiveDashboardInventoryAlert = {
  product_id: string;
  name: string;
  stock: number;
  min_stock: number;
  status: string;
};

export type ExecutiveDashboardLeadAbandoned = {
  deal_id: string;
  title: string;
  stage: string;
  days_inactive: number;
  value: number;
};

export type ExecutiveDashboardConversationUnanswered = {
  conversation_id: string;
  customer_name: string | null;
  channel: string;
  last_message_at: string | null;
  hours_silent: number;
};

export type ExecutiveDashboardInactiveCustomer = {
  customer_id: string;
  full_name: string;
  days_inactive: number;
  last_purchase_at: string | null;
};

export type ExecutiveDashboardDelayedOrder = {
  order_id: string;
  order_number: string;
  customer_name: string;
  status: string;
  days_since_created: number;
  total: number;
};

export type ExecutiveDashboardAlerts = {
  inventory_critical: ExecutiveDashboardInventoryAlert[];
  leads_abandoned: ExecutiveDashboardLeadAbandoned[];
  conversations_unanswered: ExecutiveDashboardConversationUnanswered[];
  inactive_customers: ExecutiveDashboardInactiveCustomer[];
  delayed_orders: ExecutiveDashboardDelayedOrder[];
};

export type ExecutiveDashboardMetadata = {
  tenant_id: string;
  computed_in_ms: number;
};

export type ExecutiveDashboardResponse = {
  generated_at: string;
  period: ExecutiveDashboardPeriod;
  currency: string;
  kpis: ExecutiveDashboardKpis;
  sales_trend: ExecutiveDashboardSalesTrend;
  pipeline: ExecutiveDashboardPipeline;
  ai_recommendations: ExecutiveDashboardRecommendation[];
  forecast: ExecutiveDashboardForecast;
  top_customers: ExecutiveDashboardTopCustomer[];
  top_products: ExecutiveDashboardTopProducts;
  alerts: ExecutiveDashboardAlerts;
  metadata: ExecutiveDashboardMetadata;
};
