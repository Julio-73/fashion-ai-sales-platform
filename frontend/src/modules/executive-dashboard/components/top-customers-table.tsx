"use client";

import { Crown } from "lucide-react";
import Link from "next/link";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import type { ExecutiveDashboardTopCustomer } from "@/types/executive-dashboard";

type TopCustomersTableProps = {
  customers: ExecutiveDashboardTopCustomer[];
  isLoading: boolean;
};

const currencyFormatter = new Intl.NumberFormat("es-PE", {
  style: "currency",
  currency: "PEN",
  maximumFractionDigits: 0,
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

export function TopCustomersTable({ customers, isLoading }: TopCustomersTableProps) {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-sm">Top 10 clientes</CardTitle>
            <p className="mt-1 text-xs text-muted-foreground">
              Clientes con mayor valor de vida y ticket promedio en los últimos 12 meses.
            </p>
          </div>
          <span className="rounded-full bg-secondary px-2 py-0.5 text-xs font-medium text-muted-foreground">
            {customers.length}
          </span>
        </div>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="space-y-2">
            {Array.from({ length: 5 }).map((_, i) => (
              <Skeleton key={i} className="h-10 w-full" />
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
                <tr className="border-b text-left text-[11px] uppercase tracking-wide text-muted-foreground">
                  <th className="pb-2 pr-3 font-medium">#</th>
                  <th className="pb-2 pr-3 font-medium">Cliente</th>
                  <th className="pb-2 pr-3 font-medium">Pedidos</th>
                  <th className="pb-2 pr-3 font-medium">Ticket prom.</th>
                  <th className="pb-2 pr-3 font-medium">Valor de vida</th>
                  <th className="pb-2 font-medium">Última compra</th>
                </tr>
              </thead>
              <tbody>
                {customers.slice(0, 10).map((customer, index) => (
                  <tr
                    key={customer.id}
                    className="border-b last:border-0 transition-colors hover:bg-muted/50"
                  >
                    <td className="py-2.5 pr-3 text-xs font-medium text-muted-foreground">
                      {index + 1}
                    </td>
                    <td className="py-2.5 pr-3">
                      <Link
                        href={`/dashboard/customers/${customer.id}`}
                        className="flex items-center gap-2 font-medium text-foreground hover:text-primary"
                      >
                        {customer.is_vip ? (
                          <Crown className="h-3.5 w-3.5 shrink-0 text-amber-500" />
                        ) : null}
                        <span className="truncate">{customer.full_name}</span>
                      </Link>
                    </td>
                    <td className="py-2.5 pr-3 text-muted-foreground">
                      {numberFormatter.format(customer.order_count)}
                    </td>
                    <td className="py-2.5 pr-3 font-mono text-xs text-foreground">
                      {currencyFormatter.format(customer.average_ticket)}
                    </td>
                    <td className="py-2.5 pr-3 font-mono text-xs font-semibold text-foreground">
                      {currencyFormatter.format(customer.lifetime_value)}
                    </td>
                    <td className="py-2.5 text-xs text-muted-foreground">
                      {lastPurchaseLabel(customer.days_since_last_purchase)}
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
