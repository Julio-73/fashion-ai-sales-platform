"use client";

import { CalendarDays, PackageCheck, Search, Truck, WalletCards } from "lucide-react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { DataTable } from "@/components/data-table/data-table";
import { DashboardSection } from "@/components/layout/dashboard-section";
import { Button } from "@/components/ui/button";
import { MetricCard } from "@/components/ui/metric-card";
import { Skeleton } from "@/components/ui/skeleton";
import { StatusBadge } from "@/components/ui/status-badge";
import { ApiError } from "@/services/api-client";
import { useAuthStore } from "@/store/auth-store";
import { getOrderMetrics, listOrders, updateOrderStatus } from "@/modules/orders/services/orders-api";
import type { OrderMetrics, OrderStatus, OrderSummary } from "@/types/order";

const statuses: Array<OrderStatus | "all"> = [
  "all",
  "pending",
  "confirmed",
  "preparing",
  "shipped",
  "delivered",
  "cancelled",
];

const statusLabel: Record<OrderStatus, string> = {
  pending: "Pendiente",
  confirmed: "Confirmado",
  preparing: "Preparando",
  shipped: "Enviado",
  delivered: "Entregado",
  cancelled: "Cancelado",
};

const statusTone: Record<OrderStatus, "success" | "warning" | "neutral"> = {
  pending: "warning",
  confirmed: "success",
  preparing: "warning",
  shipped: "neutral",
  delivered: "success",
  cancelled: "neutral",
};

const limit = 10;

function formatCurrency(value: string) {
  const amount = Number(value);
  return new Intl.NumberFormat("es-PE", {
    style: "currency",
    currency: "PEN",
    maximumFractionDigits: 0,
  }).format(Number.isFinite(amount) ? amount : 0);
}

function primaryProduct(order: OrderSummary) {
  return order.items[0]?.product_name ?? "Sin producto";
}

export function OrdersWorkspace() {
  const { accessToken, refreshSession } = useAuthStore();
  const [orders, setOrders] = useState<OrderSummary[]>([]);
  const [metrics, setMetrics] = useState<OrderMetrics | null>(null);
  const [status, setStatus] = useState<OrderStatus | "all">("all");
  const [customer, setCustomer] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [offset, setOffset] = useState(0);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const activeRef = useRef(true);

  const loadOrders = useCallback(async (retried = false) => {
    setIsLoading(true);
    setError(null);
    try {
      const [ordersResponse, metricsResponse] = await Promise.all([
        listOrders({
          accessToken: accessToken!,
          status,
          customer: customer || undefined,
          dateFrom: dateFrom || undefined,
          dateTo: dateTo || undefined,
          limit,
          offset,
        }),
        getOrderMetrics(accessToken!),
      ]);
      if (!activeRef.current) return;
      setOrders(ordersResponse.items);
      setTotal(ordersResponse.total);
      setMetrics(metricsResponse);
    } catch (err) {
      if (!activeRef.current) return;
      if (!retried && err instanceof ApiError && err.status === 401) {
        try {
          await refreshSession();
        } catch {
          setError("No se pudieron cargar los pedidos. La sesión no es válida.");
          return;
        }
        return loadOrders(true);
      }
      setError("No se pudieron cargar los pedidos. Verifica el backend y los permisos.");
    } finally {
      if (activeRef.current) setIsLoading(false);
    }
  }, [accessToken, status, customer, dateFrom, dateTo, offset, refreshSession]);

  useEffect(() => {
    if (!accessToken) return;
    activeRef.current = true;
    loadOrders();
    return () => { activeRef.current = false; };
  }, [accessToken, status, customer, dateFrom, dateTo, offset, loadOrders]);

  const handleStatusChange = useCallback(async (orderId: string, nextStatus: OrderStatus) => {
    if (!accessToken) return;
    const updated = await updateOrderStatus(accessToken, orderId, nextStatus);
    setOrders((current) => current.map((order) => (order.id === orderId ? updated : order)));
  }, [accessToken]);

  const rows = useMemo(
    () =>
      orders.map((order) => ({
        order: (
          <div>
            <p className="font-medium text-foreground">{order.order_number}</p>
            <p className="text-xs text-muted-foreground">{formatCurrency(order.total)}</p>
          </div>
        ),
        customer: (
          <div>
            <p className="font-medium text-foreground">{order.customer_name}</p>
            <p className="text-xs text-muted-foreground">
              {order.delivery_type === "delivery" ? "Delivery" : "Recojo en tienda"}
            </p>
          </div>
        ),
        product: primaryProduct(order),
        date: new Date(order.created_at).toLocaleDateString("es-PE", {
          day: "2-digit",
          month: "short",
          year: "numeric",
        }),
        status: (
          <div className="flex items-center gap-2">
            <StatusBadge tone={statusTone[order.status]}>{statusLabel[order.status]}</StatusBadge>
            <select
              className="h-8 rounded-md border bg-background px-2 text-xs outline-none focus-visible:ring-2 focus-visible:ring-ring"
              value={order.status}
              onChange={(event) => handleStatusChange(order.id, event.target.value as OrderStatus)}
            >
              {statuses.filter((item) => item !== "all").map((item) => (
                <option key={item} value={item}>
                  {statusLabel[item]}
                </option>
              ))}
            </select>
          </div>
        ),
      })),
    [orders, handleStatusChange],
  );

  return (
    <div className="grid gap-6">
      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          title="Pedidos hoy"
          value={String(metrics?.orders_today ?? 0)}
          icon={PackageCheck}
          footer={<span className="text-xs text-muted-foreground">Confirmados y gestionables desde operaciones.</span>}
        />
        <MetricCard
          title="Pedidos semana"
          value={String(metrics?.orders_week ?? 0)}
          icon={CalendarDays}
          footer={<span className="text-xs text-muted-foreground">Volumen operativo de la semana actual.</span>}
          delay={0.04}
        />
        <MetricCard
          title="Pedidos mes"
          value={String(metrics?.orders_month ?? 0)}
          icon={Truck}
          footer={<span className="text-xs text-muted-foreground">Seguimiento mensual de fulfilment.</span>}
          delay={0.08}
        />
        <MetricCard
          title="Ventas totales"
          value={formatCurrency(metrics?.total_sales ?? "0")}
          icon={WalletCards}
          footer={<span className="text-xs text-muted-foreground">Excluye pedidos cancelados.</span>}
          delay={0.12}
        />
      </section>

      <div className="rounded-lg border bg-card p-4 shadow-sm">
        <div className="grid gap-3 lg:grid-cols-[minmax(0,1fr)_180px_180px_180px_auto]">
          <div className="relative">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <input
              className="h-10 w-full rounded-md border bg-background pl-9 pr-3 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
              placeholder="Buscar por cliente o teléfono"
              value={customer}
              onChange={(event) => {
                setCustomer(event.target.value);
                setOffset(0);
              }}
            />
          </div>
          <select
            className="h-10 rounded-md border bg-background px-3 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
            value={status}
            onChange={(event) => {
              setStatus(event.target.value as OrderStatus | "all");
              setOffset(0);
            }}
          >
            {statuses.map((item) => (
              <option key={item} value={item}>
                {item === "all" ? "Todos los estados" : statusLabel[item]}
              </option>
            ))}
          </select>
          <input
            type="date"
            className="h-10 rounded-md border bg-background px-3 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
            value={dateFrom}
            onChange={(event) => {
              setDateFrom(event.target.value);
              setOffset(0);
            }}
          />
          <input
            type="date"
            className="h-10 rounded-md border bg-background px-3 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
            value={dateTo}
            onChange={(event) => {
              setDateTo(event.target.value);
              setOffset(0);
            }}
          />
          <Button
            type="button"
            variant="outline"
            onClick={() => {
              setCustomer("");
              setStatus("all");
              setDateFrom("");
              setDateTo("");
              setOffset(0);
            }}
          >
            Limpiar
          </Button>
        </div>
      </div>

      {error ? (
        <div className="rounded-lg border border-destructive/25 bg-destructive/10 px-4 py-3 text-sm text-destructive">
          {error}
        </div>
      ) : null}

      <DashboardSection
        title="Pedidos operativos"
        description={`${total} ${total === 1 ? "pedido" : "pedidos"} encontrados`}
      >
        {isLoading ? (
          <div className="grid gap-3">
            {Array.from({ length: 4 }).map((_, index) => (
              <Skeleton key={index} className="h-16 w-full" />
            ))}
          </div>
        ) : (
          <>
            <DataTable
              columns={[
                { key: "order", header: "Pedido" },
                { key: "customer", header: "Cliente" },
                { key: "product", header: "Producto" },
                { key: "date", header: "Fecha" },
                { key: "status", header: "Estado" },
              ]}
              rows={rows}
              emptyTitle="Sin pedidos"
              emptyDescription="Los pedidos confirmados por la IA aparecerán aquí automáticamente."
            />
            <div className="flex items-center justify-between pt-4 text-sm text-muted-foreground">
              <span>
                {total > 0
                  ? `Mostrando ${offset + 1}-${offset + orders.length} de ${total}`
                  : "No se encontraron pedidos"}
              </span>
              <div className="flex gap-2">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  disabled={offset === 0}
                  onClick={() => setOffset((current) => Math.max(0, current - limit))}
                >
                  Anterior
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  disabled={offset + limit >= total}
                  onClick={() => setOffset((current) => current + limit)}
                >
                  Siguiente
                </Button>
              </div>
            </div>
          </>
        )}
      </DashboardSection>
    </div>
  );
}
