"use client";

import {
  AlertTriangle,
  Boxes,
  CircleDollarSign,
  PackageCheck,
  PackageX,
  Search,
} from "lucide-react";
import Link from "next/link";
import { useEffect, useMemo, useRef, useState } from "react";

import { DataTable } from "@/components/data-table/data-table";
import { DashboardSection } from "@/components/layout/dashboard-section";
import { Button } from "@/components/ui/button";
import { MetricCard } from "@/components/ui/metric-card";
import { Skeleton } from "@/components/ui/skeleton";
import { StatusBadge } from "@/components/ui/status-badge";
import { ApiError } from "@/services/api-client";
import { useAuthStore } from "@/store/auth-store";
import { getInventoryMetrics, listInventory } from "@/modules/inventory/services/inventory-api";
import type {
  InventoryAggregateMetrics,
  InventoryProductSummary,
  InventoryStatus,
  InventoryStatusFilter,
} from "@/types/inventory";

const statusFilters: InventoryStatusFilter[] = ["all", "normal", "stock_bajo", "agotado"];

const statusLabel: Record<InventoryStatus, string> = {
  normal: "Normal",
  stock_bajo: "Stock bajo",
  agotado: "Agotado",
};

const statusTone: Record<InventoryStatus, "success" | "warning" | "neutral"> = {
  normal: "success",
  stock_bajo: "warning",
  agotado: "neutral",
};

const limit = 10;

function formatCurrency(value: string): string {
  const amount = Number(value);
  return new Intl.NumberFormat("es-PE", {
    style: "currency",
    currency: "PEN",
    maximumFractionDigits: 2,
  }).format(Number.isFinite(amount) ? amount : 0);
}

function formatDate(iso: string | null): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString("es-PE", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

function StockBar({ actual, minimo }: { actual: number; minimo: number }) {
  const ratio = minimo > 0 ? Math.min(1.5, actual / minimo) : actual > 0 ? 1.5 : 0;
  const pct = Math.max(0, Math.min(100, (ratio / 1.5) * 100));
  const tone = actual <= 0 ? "destructive" : actual <= minimo ? "warning" : "success";
  const colorClass =
    tone === "destructive"
      ? "bg-destructive"
      : tone === "warning"
        ? "bg-amber-500"
        : "bg-emerald-500";
  return (
    <div className="h-1.5 w-24 overflow-hidden rounded-full bg-secondary">
      <div className={`h-full ${colorClass}`} style={{ width: `${pct}%` }} />
    </div>
  );
}

export function InventoryWorkspace() {
  const { accessToken, refreshSession } = useAuthStore();
  const [items, setItems] = useState<InventoryProductSummary[]>([]);
  const [total, setTotal] = useState(0);
  const [metrics, setMetrics] = useState<InventoryAggregateMetrics | null>(null);
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState<InventoryStatusFilter>("all");
  const [offset, setOffset] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const activeRef = useRef(true);

  useEffect(() => {
    if (!accessToken) return;
    activeRef.current = true;
    load();
    return () => {
      activeRef.current = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [accessToken, search, status, offset]);

  async function load(retried = false) {
    if (!accessToken) return;
    setIsLoading(true);
    setError(null);
    try {
      const [listResponse, metricsResponse] = await Promise.all([
        listInventory({
          accessToken,
          search: search || undefined,
          status,
          limit,
          offset,
        }),
        getInventoryMetrics(accessToken),
      ]);
      if (!activeRef.current) return;
      setItems(listResponse.items);
      setTotal(listResponse.total);
      setMetrics(metricsResponse);
    } catch (err) {
      if (!activeRef.current) return;
      if (!retried && err instanceof ApiError && err.status === 401) {
        try {
          await refreshSession();
        } catch {
          setError("No se pudo cargar el inventario. La sesión no es válida.");
          setIsLoading(false);
          return;
        }
        return load(true);
      }
      setError("No se pudo cargar el inventario. Verifica el backend y los permisos.");
    } finally {
      if (activeRef.current) setIsLoading(false);
    }
  }

  const rows = useMemo(
    () =>
      items.map((item) => ({
        id: item.product_id,
        product: (
          <Link
            href={`/dashboard/inventory/${item.product_id}`}
            className="font-medium text-foreground hover:underline"
          >
            {item.name}
          </Link>
        ),
        category: item.category ?? "—",
        stockActual: (
          <div className="flex items-center gap-2">
            <span className="font-medium">{item.stock_actual}</span>
            <StockBar actual={item.stock_actual} minimo={item.stock_minimo} />
          </div>
        ),
        reservado: item.stock_reservado,
        disponible: (
          <span className={item.stock_disponible <= 0 ? "font-semibold text-destructive" : ""}>
            {item.stock_disponible}
          </span>
        ),
        status: <StatusBadge tone={statusTone[item.status]}>{statusLabel[item.status]}</StatusBadge>,
        updated: formatDate(item.last_movement_at ?? item.updated_at),
      })),
    [items],
  );

  return (
    <div className="grid gap-6">
      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          title="Total productos"
          value={String(metrics?.total_products ?? 0)}
          icon={Boxes}
          footer={
            <span className="text-xs text-muted-foreground">
              {metrics?.total_units ?? 0} unidades en stock
            </span>
          }
        />
        <MetricCard
          title="Stock bajo"
          value={String(metrics?.low_stock ?? 0)}
          icon={AlertTriangle}
          footer={
            <span className="text-xs text-muted-foreground">
              Productos cerca del mínimo configurado
            </span>
          }
          delay={0.04}
        />
        <MetricCard
          title="Agotados"
          value={String(metrics?.out_of_stock ?? 0)}
          icon={PackageX}
          footer={
            <span className="text-xs text-muted-foreground">
              Requieren reposición inmediata
            </span>
          }
          delay={0.08}
        />
        <MetricCard
          title="Valor de inventario"
          value={formatCurrency(metrics?.inventory_value ?? "0")}
          icon={CircleDollarSign}
          footer={
            <span className="text-xs text-muted-foreground">
              {metrics?.total_reserved_units ?? 0} unidades reservadas
            </span>
          }
          delay={0.12}
        />
      </section>

      {metrics && (metrics.out_of_stock > 0 || metrics.low_stock > 0) ? (
        <section
          className={`rounded-lg border px-4 py-3 text-sm ${
            metrics.out_of_stock > 0
              ? "border-destructive/30 bg-destructive/10 text-destructive"
              : "border-amber-300 bg-amber-50 text-amber-900"
          }`}
        >
          <div className="flex items-center gap-2 font-medium">
            <AlertTriangle className="h-4 w-4" />
            {metrics.out_of_stock > 0
              ? `${metrics.out_of_stock} producto${metrics.out_of_stock === 1 ? "" : "s"} agotado${
                  metrics.out_of_stock === 1 ? "" : "s"
                }`
              : `${metrics.low_stock} producto${metrics.low_stock === 1 ? "" : "s"} con stock bajo`}
          </div>
          <p className="mt-1 text-xs opacity-80">
            Revisa la tabla y genera reposición para mantener disponibilidad.
          </p>
        </section>
      ) : null}

      <div className="rounded-lg border bg-card p-4 shadow-sm">
        <div className="grid gap-3 lg:grid-cols-[minmax(0,1fr)_220px_auto]">
          <div className="relative">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <input
              className="h-10 w-full rounded-md border bg-background pl-9 pr-3 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
              placeholder="Buscar por nombre, slug o categoría…"
              value={search}
              onChange={(event) => {
                setSearch(event.target.value);
                setOffset(0);
              }}
            />
          </div>
          <select
            className="h-10 rounded-md border bg-background px-3 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
            value={status}
            onChange={(event) => {
              setStatus(event.target.value as InventoryStatusFilter);
              setOffset(0);
            }}
          >
            {statusFilters.map((s) => (
              <option key={s} value={s}>
                {s === "all" ? "Todos los estados" : statusLabel[s]}
              </option>
            ))}
          </select>
          <Button
            type="button"
            variant="outline"
            onClick={() => {
              setSearch("");
              setStatus("all");
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
        title="Inventario"
        description={`${total} ${total === 1 ? "producto" : "productos"} encontrados`}
      >
        {isLoading ? (
          <div className="grid gap-3">
            {Array.from({ length: 4 }).map((_, index) => (
              <Skeleton key={index} className="h-12 w-full" />
            ))}
          </div>
        ) : (
          <>
            <DataTable
              columns={[
                { key: "product", header: "Producto" },
                { key: "category", header: "Categoría" },
                { key: "stockActual", header: "Stock actual" },
                { key: "reservado", header: "Reservado" },
                { key: "disponible", header: "Disponible" },
                { key: "status", header: "Estado" },
                { key: "updated", header: "Última actualización" },
              ]}
              rows={rows}
              emptyTitle="Sin productos en inventario"
              emptyDescription="Ajusta los filtros o crea productos para empezar a registrar stock."
            />
            <div className="flex items-center justify-between pt-4 text-sm text-muted-foreground">
              <span>
                {total > 0
                  ? `Mostrando ${offset + 1}-${offset + items.length} de ${total}`
                  : "No se encontraron productos"}
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

      {metrics && metrics.lowest_stock_products.length > 0 ? (
        <DashboardSection
          title="Productos con menor stock"
          description="Top 5 que requieren atención"
        >
          <ul className="grid gap-2 md:grid-cols-2 xl:grid-cols-3">
            {metrics.lowest_stock_products.map((item) => (
              <li
                key={item.product_id}
                className="flex items-center justify-between rounded-md border bg-background px-3 py-2 text-sm"
              >
                <div className="min-w-0 flex-1">
                  <p className="truncate font-medium">{item.name}</p>
                  <p className="text-xs text-muted-foreground">
                    Actual: {item.stock_actual} · Mínimo: {item.stock_minimo}
                  </p>
                </div>
                <StatusBadge tone={statusTone[item.status]}>
                  {statusLabel[item.status]}
                </StatusBadge>
              </li>
            ))}
          </ul>
        </DashboardSection>
      ) : null}
    </div>
  );
}
