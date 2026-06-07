"use client";

import { Crown } from "lucide-react";
import Link from "next/link";

import { Avatar } from "@/components/ui/avatar";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { StatusPill } from "@/components/ui/status-pill";
import type { ExecutiveDashboardTopCustomer } from "@/types/executive-dashboard";

type TopCustomersTableProps = {
  customers: ExecutiveDashboardTopCustomer[];
  isLoading: boolean;
};

const currencyFormatter = new Intl.NumberFormat("es-PE", {
  style: "currency",
  currency: "PEN",
  maximumFractionDigits: 0
});

const numberFormatter = new Intl.NumberFormat("es-PE");

function lastPurchaseLabel(days: number | null) {
  if (days === null) return "Sin compras";
  if (days === 0) return "Hoy";
  if (days === 1) return "Ayer";
  if (days < 7) return `Hace ${days} días`;
  if (days < 30) return `Hace ${Math.floor(days / 7)} sem.`;
  if (days < 365) return `Hace ${Math.floor(days / 30)} meses`;
  return `Hace ${Math.floor(days / 365)} años`;
}

export function TopCustomersTable({
  customers,
  isLoading
}: TopCustomersTableProps) {
  return (
    <Card variant="elevated">
      <CardContent>
        <div className="mb-4 flex items-center justify-between">
          <div>
            <h3 className="text-sm font-semibold tracking-tight">
              Top 10 clientes
            </h3>
            <p className="mt-0.5 text-xs text-muted-foreground">
              Clientes con mayor valor de vida y ticket promedio en los últimos
              12 meses.
            </p>
          </div>
          <span className="rounded-full bg-secondary px-2.5 py-0.5 text-xs font-semibold text-muted-foreground">
            {customers.length}
          </span>
        </div>
        {isLoading ? (
          <div className="space-y-2">
            {Array.from({ length: 5 }).map((_, i) => (
              <Skeleton key={i} className="h-12 w-full" />
            ))}
          </div>
        ) : customers.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            Aún no hay clientes con historial suficiente.
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-left text-[11px] uppercase tracking-wider text-muted-foreground">
                  <th className="pb-2 pr-3 font-semibold">#</th>
                  <th className="pb-2 pr-3 font-semibold">Cliente</th>
                  <th className="pb-2 pr-3 font-semibold">Pedidos</th>
                  <th className="pb-2 pr-3 font-semibold">Ticket prom.</th>
                  <th className="pb-2 pr-3 font-semibold">Valor de vida</th>
                  <th className="pb-2 font-semibold">Última compra</th>
                </tr>
              </thead>
              <tbody>
                {customers.slice(0, 10).map((customer, index) => (
                  <tr
                    key={customer.id}
                    className="border-b border-border/60 transition-colors last:border-0 hover:bg-secondary/40"
                  >
                    <td className="py-3 pr-3 text-xs font-mono text-muted-foreground">
                      {(index + 1).toString().padStart(2, "0")}
                    </td>
                    <td className="py-3 pr-3">
                      <Link
                        href={`/dashboard/customers/${customer.id}`}
                        className="flex items-center gap-2.5 font-medium text-foreground transition-colors hover:text-primary"
                      >
                        <Avatar name={customer.full_name} size="sm" />
                        <div className="flex min-w-0 flex-col">
                          <span className="flex items-center gap-1.5 truncate">
                            {customer.full_name}
                            {customer.is_vip ? (
                              <Crown
                                className="h-3 w-3 shrink-0 text-amber-500"
                                aria-label="VIP"
                              />
                            ) : null}
                          </span>
                          {customer.is_vip ? (
                            <span className="text-[10px] font-medium text-amber-600 dark:text-amber-400">
                              Cliente VIP
                            </span>
                          ) : null}
                        </div>
                      </Link>
                    </td>
                    <td className="py-3 pr-3 text-muted-foreground">
                      {numberFormatter.format(customer.order_count)}
                    </td>
                    <td className="py-3 pr-3 font-mono text-xs text-foreground">
                      {currencyFormatter.format(customer.average_ticket)}
                    </td>
                    <td className="py-3 pr-3 font-mono text-xs font-semibold text-foreground">
                      {currencyFormatter.format(customer.lifetime_value)}
                    </td>
                    <td className="py-3 text-xs text-muted-foreground">
                      <StatusPill
                        tone={
                          customer.days_since_last_purchase === null
                            ? "neutral"
                            : customer.days_since_last_purchase > 60
                              ? "warning"
                              : "success"
                        }
                        size="sm"
                      >
                        {lastPurchaseLabel(customer.days_since_last_purchase)}
                      </StatusPill>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
