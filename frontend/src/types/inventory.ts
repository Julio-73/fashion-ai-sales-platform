export type InventoryStatus = "normal" | "stock_bajo" | "agotado";
export type InventoryStatusFilter = "all" | "normal" | "stock_bajo" | "agotado";
export type InventorySortBy =
  | "name"
  | "stock_actual"
  | "stock_disponible"
  | "last_movement_at"
  | "category";

export type InventoryMovementTipo =
  | "entrada"
  | "salida"
  | "reserva"
  | "liberacion"
  | "ajuste";

export type InventoryReservationStatus = "active" | "cancelled" | "released" | "expired";

export type InventoryProductSummary = {
  product_id: string;
  name: string;
  category: string | null;
  base_price: string | null;
  sku: string | null;
  image_url: string | null;
  stock_actual: number;
  stock_minimo: number;
  stock_reservado: number;
  stock_disponible: number;
  status: InventoryStatus;
  last_movement_at: string | null;
  updated_at: string;
};

export type InventoryListResponse = {
  items: InventoryProductSummary[];
  total: number;
  limit: number;
  offset: number;
};

export type InventoryMovement = {
  id: string;
  product_id: string;
  tipo: InventoryMovementTipo;
  cantidad: number;
  motivo: string | null;
  ref_type: string | null;
  ref_id: string | null;
  created_at: string;
};

export type InventoryReservation = {
  id: string;
  product_id: string;
  quantity: number;
  status: InventoryReservationStatus;
  ref_type: string | null;
  ref_id: string | null;
  expires_at: string | null;
  created_at: string;
  updated_at: string;
};

export type InventoryTopProduct = {
  product_id: string;
  name: string;
  units_sold: number;
  revenue: string;
};

export type InventoryLowStockProduct = {
  product_id: string;
  name: string;
  stock_actual: number;
  stock_minimo: number;
  status: InventoryStatus;
};

export type InventoryAggregateMetrics = {
  total_products: number;
  out_of_stock: number;
  low_stock: number;
  normal_stock: number;
  inventory_value: string;
  total_units: number;
  total_reserved_units: number;
  top_selling_products: InventoryTopProduct[];
  lowest_stock_products: InventoryLowStockProduct[];
};

export type InventoryProductDetail = {
  product: InventoryProductSummary;
  recent_movements: InventoryMovement[];
  active_reservations: InventoryReservation[];
  metrics: InventoryAggregateMetrics;
};
