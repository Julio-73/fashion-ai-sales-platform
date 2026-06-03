"use client";

import {
  AlertTriangle,
  ArrowDownCircle,
  ArrowUpCircle,
  CircleDollarSign,
  History,
  PackageCheck,
  PackageX,
} from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";

import { DashboardSection } from "@/components/layout/dashboard-section";
import { Skeleton } from "@/components/ui/skeleton";
import { StatusBadge } from "@/components/ui/status-badge";
import { ApiError } from "@/services/api-client";
import { useAuthStore } from "@/store/auth-store";
import { getInventoryProduct } from "@/modules/inventory/services/inventory-api";
import type {
  InventoryMovement,
  InventoryMovementTipo,
  InventoryProductDetail,
  InventoryReservation,
  InventoryStatus,
} from "@/types/inventory";

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

const movementTone: Record<
  InventoryMovementTipo,
  "success" | "warning" | "neutral"
> = {
  entrada: "success",
  salida: "neutral",
  reserva: "warning",
  liberacion: "neutral",
  ajuste: "neutral",
};

const movementLabel: Record<InventoryMovementTipo, string> = {
  entrada: "Entrada",
  salida: "Salida",
  reserva: "Reserva",
  liberacion: "Liberación",
  ajuste: "Ajuste",
};

const reservationLabel: Record<string, string> = {
  active: "Activa",
  cancelled: "Cancelada",
  released: "Liberada",
  expired: "Expirada",
};

function formatCurrency(value: string | null): string {
  if (value == null) return "—";
  const amount = Number(value);
  return new Intl.NumberFormat("es-PE", {
    style: "currency",
    currency: "PEN",
    maximumFractionDigits: 2,
  }).format(Number.isFinite(amount) ? amount : 0);
}

function formatDate(iso: string | null): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleString("es-PE", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function MovementIcon({ tipo }: { tipo: InventoryMovementTipo }) {
  if (tipo === "entrada" || tipo === "liberacion") {
    return <ArrowUpCircle className="h-4 w-4 text-emerald-600" aria-hidden="true" />;
  }
  return <ArrowDownCircle className="h-4 w-4 text-destructive" aria-hidden="true" />;
}

type InventoryDetailProps = {
  productId: string;
};

export function InventoryDetail({ productId }: InventoryDetailProps) {
  const { accessToken, refreshSession } = useAuthStore();
  const [data, setData] = useState<InventoryProductDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!accessToken) return;
    let active = true;
    setIsLoading(true);
    setError(null);

    (async () => {
      try {
        const detail = await getInventoryProduct(accessToken, productId);
        if (!active) return;
        setData(detail);
      } catch (err) {
        if (!active) return;
        if (err instanceof ApiError && err.status === 401) {
          try {
            await refreshSession();
            return;
          } catch {
            setError("La sesión no es válida. Vuelve a iniciar sesión.");
            setIsLoading(false);
            return;
          }
        }
        setError("No se pudo cargar el detalle de inventario.");
      } finally {
        if (active) setIsLoading(false);
      }
    })();

    return () => {
      active = false;
    };
  }, [accessToken, productId, refreshSession]);

  if (isLoading) {
    return (
      <div className="grid gap-4">
        {Array.from({ length: 3 }).map((_, i) => (
          <Skeleton key={i} className="h-24 w-full" />
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="grid gap-3">
        <div className="rounded-lg border border-destructive/25 bg-destructive/10 px-4 py-3 text-sm text-destructive">
          {error}
        </div>
        <Link
          href="/dashboard/inventory"
          className="text-sm text-muted-foreground hover:underline"
        >
          ← Volver al inventario
        </Link>
      </div>
    );
  }

  if (!data) return null;

  const { product, recent_movements, active_reservations, metrics } = data;
  const alerts: string[] = [];
  if (product.status === "agotado") alerts.push("Producto agotado");
  if (product.status === "stock_bajo") alerts.push("Stock por debajo del mínimo");
  if (product.stock_reservado > product.stock_actual) {
    alerts.push("Reservado supera al stock actual");
  }

  return (
    <div className="grid gap-6">
      <Link
        href="/dashboard/inventory"
        className="text-sm text-muted-foreground hover:underline"
      >
        ← Volver al inventario
      </Link>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <div className="rounded-lg border bg-card p-4 shadow-sm">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-xs uppercase tracking-wide text-muted-foreground">Stock actual</p>
              <p className="mt-2 text-2xl font-semibold">{product.stock_actual}</p>
            </div>
            <PackageCheck className="h-5 w-5 text-emerald-600" />
          </div>
          <p className="mt-2 text-xs text-muted-foreground">Mínimo: {product.stock_minimo}</p>
        </div>
        <div className="rounded-lg border bg-card p-4 shadow-sm">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-xs uppercase tracking-wide text-muted-foreground">Reservado</p>
              <p className="mt-2 text-2xl font-semibold">{product.stock_reservado}</p>
            </div>
            <History className="h-5 w-5 text-amber-500" />
          </div>
          <p className="mt-2 text-xs text-muted-foreground">En reservas activas</p>
        </div>
        <div className="rounded-lg border bg-card p-4 shadow-sm">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-xs uppercase tracking-wide text-muted-foreground">Disponible</p>
              <p
                className={`mt-2 text-2xl font-semibold ${
                  product.stock_disponible <= 0 ? "text-destructive" : ""
                }`}
              >
                {product.stock_disponible}
              </p>
            </div>
            <PackageX
              className={`h-5 w-5 ${
                product.stock_disponible <= 0 ? "text-destructive" : "text-muted-foreground"
              }`}
            />
          </div>
          <p className="mt-2 text-xs text-muted-foreground">Actual − Reservado</p>
        </div>
        <div className="rounded-lg border bg-card p-4 shadow-sm">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-xs uppercase tracking-wide text-muted-foreground">
                Precio base
              </p>
              <p className="mt-2 text-2xl font-semibold">
                {formatCurrency(product.base_price)}
              </p>
            </div>
            <CircleDollarSign className="h-5 w-5 text-muted-foreground" />
          </div>
          <p className="mt-2 text-xs text-muted-foreground">SKU: {product.sku ?? "—"}</p>
        </div>
      </section>

      <section className="grid gap-4 lg:grid-cols-[2fr_1fr]">
        <div className="rounded-lg border bg-card p-5 shadow-sm">
          <div className="flex items-start justify-between gap-3">
            <div>
              <h2 className="text-lg font-semibold">{product.name}</h2>
              <p className="text-xs text-muted-foreground">
                {product.category ?? "Sin categoría"} · Actualizado{" "}
                {formatDate(product.last_movement_at ?? product.updated_at)}
              </p>
            </div>
            <StatusBadge tone={statusTone[product.status]}>
              {statusLabel[product.status]}
            </StatusBadge>
          </div>
          {alerts.length > 0 ? (
            <ul className="mt-4 space-y-1">
              {alerts.map((msg) => (
                <li
                  key={msg}
                  className="flex items-center gap-2 rounded-md border border-amber-300 bg-amber-50 px-3 py-2 text-sm text-amber-900"
                >
                  <AlertTriangle className="h-4 w-4" />
                  {msg}
                </li>
              ))}
            </ul>
          ) : null}
        </div>
        <div className="rounded-lg border bg-card p-5 shadow-sm">
          <h3 className="text-sm font-semibold">Resumen general</h3>
          <dl className="mt-3 grid grid-cols-2 gap-2 text-sm">
            <dt className="text-muted-foreground">Total productos</dt>
            <dd className="text-right font-medium">{metrics.total_products}</dd>
            <dt className="text-muted-foreground">Stock bajo</dt>
            <dd className="text-right font-medium">{metrics.low_stock}</dd>
            <dt className="text-muted-foreground">Agotados</dt>
            <dd className="text-right font-medium">{metrics.out_of_stock}</dd>
            <dt className="text-muted-foreground">Valor inventario</dt>
            <dd className="text-right font-medium">
              {formatCurrency(metrics.inventory_value)}
            </dd>
            <dt className="text-muted-foreground">Unidades reservadas</dt>
            <dd className="text-right font-medium">{metrics.total_reserved_units}</dd>
          </dl>
        </div>
      </section>

      <DashboardSection
        title="Historial de movimientos"
        description={`Últimos ${recent_movements.length} movimientos registrados`}
      >
        {recent_movements.length === 0 ? (
          <p className="rounded-md border border-dashed bg-background px-4 py-6 text-center text-sm text-muted-foreground">
            Sin movimientos registrados todavía.
          </p>
        ) : (
          <ul className="divide-y rounded-md border bg-background">
            {recent_movements.map((movement: InventoryMovement) => (
              <li
                key={movement.id}
                className="flex flex-col gap-1 px-4 py-3 text-sm sm:flex-row sm:items-center sm:justify-between"
              >
                <div className="flex items-center gap-3">
                  <MovementIcon tipo={movement.tipo} />
                  <div>
                    <p className="font-medium">
                      {movementLabel[movement.tipo]} · {movement.cantidad} ud.
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {movement.motivo ?? "Sin motivo"}{" "}
                      {movement.ref_type
                        ? `· ref: ${movement.ref_type}${movement.ref_id ? ` (${movement.ref_id.slice(0, 8)}…)` : ""}`
                        : ""}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <StatusBadge tone={movementTone[movement.tipo]}>
                    {movementLabel[movement.tipo]}
                  </StatusBadge>
                  <span className="text-xs text-muted-foreground">
                    {formatDate(movement.created_at)}
                  </span>
                </div>
              </li>
            ))}
          </ul>
        )}
      </DashboardSection>

      <DashboardSection
        title="Reservas activas"
        description={`${active_reservations.length} reserva${active_reservations.length === 1 ? "" : "s"} en curso`}
      >
        {active_reservations.length === 0 ? (
          <p className="rounded-md border border-dashed bg-background px-4 py-6 text-center text-sm text-muted-foreground">
            No hay reservas activas para este producto.
          </p>
        ) : (
          <ul className="grid gap-2 md:grid-cols-2">
            {active_reservations.map((reservation: InventoryReservation) => (
              <li
                key={reservation.id}
                className="rounded-md border bg-background p-3 text-sm"
              >
                <div className="flex items-center justify-between">
                  <span className="font-medium">
                    {reservation.quantity} ud. reservadas
                  </span>
                  <StatusBadge tone="warning">
                    {reservationLabel[reservation.status] ?? reservation.status}
                  </StatusBadge>
                </div>
                <p className="mt-1 text-xs text-muted-foreground">
                  {reservation.ref_type
                    ? `Origen: ${reservation.ref_type}`
                    : "Origen manual"}
                </p>
                <p className="text-xs text-muted-foreground">
                  Creada {formatDate(reservation.created_at)}
                </p>
                {reservation.expires_at ? (
                  <p className="text-xs text-muted-foreground">
                    Expira {formatDate(reservation.expires_at)}
                  </p>
                ) : null}
              </li>
            ))}
          </ul>
        )}
      </DashboardSection>
    </div>
  );
}
