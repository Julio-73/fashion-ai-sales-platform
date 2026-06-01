export type OrderStatus = "pending" | "confirmed" | "preparing" | "shipped" | "delivered" | "cancelled";

export type DeliveryType = "delivery" | "store_pickup";

export type OrderItem = {
  id: string;
  order_id: string;
  empresa_id: string;
  product_id: string | null;
  product_name: string;
  size: string | null;
  color: string | null;
  quantity: number;
  price: string;
  created_at: string;
  updated_at: string;
};

export type OrderSummary = {
  id: string;
  empresa_id: string;
  order_number: string;
  customer_name: string;
  customer_phone: string | null;
  delivery_type: DeliveryType;
  delivery_address: string | null;
  status: OrderStatus;
  total: string;
  items: OrderItem[];
  created_at: string;
  updated_at: string;
};

export type OrderListResponse = {
  items: OrderSummary[];
  total: number;
  limit: number;
  offset: number;
};

export type OrderMetrics = {
  orders_today: number;
  orders_week: number;
  orders_month: number;
  total_sales: string;
};
