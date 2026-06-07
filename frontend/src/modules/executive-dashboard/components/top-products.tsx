"use client";

import {
  Award,
  Eye,
  LineChart,
  ShoppingBag,
  type LucideIcon
} from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { StatusPill } from "@/components/ui/status-pill";
import { cn } from "@/lib/utils";
import type { ExecutiveDashboardTopProducts } from "@/types/executive-dashboard";

type TopProductsProps = {
  data: ExecutiveDashboardTopProducts | null;
  isLoading: boolean;
};

const currencyFormatter = new Intl.NumberFormat("es-PE", {
  style: "currency",
  currency: "PEN",
  maximumFractionDigits: 0
});

const numberFormatter = new Intl.NumberFormat("es-PE");

type ProductColumnProps = {
  title: string;
  icon: LucideIcon;
  items: Array<{ name: string; primary: string; secondary: string }>;
  isLoading: boolean;
  emptyMessage: string;
  accent:
    | "bg-emerald-50 text-emerald-700 ring-emerald-200 dark:bg-emerald-50/20 dark:text-emerald-200 dark:ring-emerald-200/30"
    | "bg-amber-50 text-amber-700 ring-amber-200 dark:bg-amber-50/20 dark:text-amber-200 dark:ring-amber-200/30"
    | "bg-blue-50 text-blue-700 ring-blue-200 dark:bg-blue-50/20 dark:text-blue-200 dark:ring-blue-200/30";
};

function ProductColumn({
  title,
  icon: Icon,
  items,
  isLoading,
  emptyMessage,
  accent
}: ProductColumnProps) {
  return (
    <div className="flex flex-col rounded-xl border bg-background p-4 transition-shadow hover:shadow-sm">
      <div className="mb-3 flex items-center gap-2">
        <div
          className={cn(
            "flex h-7 w-7 items-center justify-center rounded-md ring-1 ring-inset",
            accent
          )}
        >
          <Icon className="h-3.5 w-3.5" />
        </div>
        <p className="text-sm font-semibold tracking-tight text-foreground">
          {title}
        </p>
        <span className="ml-auto rounded-full bg-secondary px-2 py-0.5 text-[11px] font-semibold text-muted-foreground">
          {items.length}
        </span>
      </div>
      {isLoading ? (
        <div className="space-y-2">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-10 w-full" />
          ))}
        </div>
      ) : items.length === 0 ? (
        <p className="py-6 text-center text-xs text-muted-foreground">
          {emptyMessage}
        </p>
      ) : (
        <ul className="space-y-1.5">
          {items.slice(0, 5).map((item, index) => (
            <li
              key={`${item.name}-${index}`}
              className="group flex items-center justify-between gap-2 rounded-md border bg-card px-3 py-2 transition-colors hover:border-primary-200 hover:bg-primary-50/40"
            >
              <div className="flex min-w-0 flex-1 items-center gap-2">
                <span className="font-mono text-[10px] font-semibold text-muted-foreground">
                  {(index + 1).toString().padStart(2, "0")}
                </span>
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium text-foreground">
                    {item.name}
                  </p>
                  <p className="text-[11px] text-muted-foreground">
                    {item.secondary}
                  </p>
                </div>
              </div>
              <StatusPill tone="primary" size="sm">
                {item.primary}
              </StatusPill>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export function TopProducts({ data, isLoading }: TopProductsProps) {
  const mostSold = (data?.most_sold ?? []).map((p) => ({
    name: p.name,
    primary: numberFormatter.format(p.units_sold),
    secondary: `${currencyFormatter.format(p.revenue)} en ventas`
  }));
  const mostProfitable = (data?.most_profitable ?? []).map((p) => ({
    name: p.name,
    primary: currencyFormatter.format(p.revenue),
    secondary: `${numberFormatter.format(p.units_sold)} unidades`
  }));
  const mostConsulted = (data?.most_consulted ?? []).map((p) => ({
    name: p.name,
    primary: numberFormatter.format(p.mentions),
    secondary: "Consultas en conversaciones"
  }));

  return (
    <Card variant="elevated">
      <CardContent>
        <div className="mb-4 flex items-center gap-2">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary-50 text-primary ring-1 ring-primary-200/60">
            <LineChart className="h-4 w-4" />
          </div>
          <div>
            <h3 className="text-sm font-semibold tracking-tight">
              Productos destacados
            </h3>
            <p className="text-xs text-muted-foreground">
              Lo más vendido, rentable y consultado por tus clientes.
            </p>
          </div>
        </div>
        <div className="grid gap-3 lg:grid-cols-3">
          <ProductColumn
            title="Más vendidos"
            icon={ShoppingBag}
            items={mostSold}
            isLoading={isLoading}
            emptyMessage="Aún no hay ventas registradas."
            accent="bg-emerald-50 text-emerald-700 ring-emerald-200 dark:bg-emerald-50/20 dark:text-emerald-200 dark:ring-emerald-200/30"
          />
          <ProductColumn
            title="Más rentables"
            icon={Award}
            items={mostProfitable}
            isLoading={isLoading}
            emptyMessage="Aún no hay ingresos registrados."
            accent="bg-amber-50 text-amber-700 ring-amber-200 dark:bg-amber-50/20 dark:text-amber-200 dark:ring-amber-200/30"
          />
          <ProductColumn
            title="Más consultados"
            icon={Eye}
            items={mostConsulted}
            isLoading={isLoading}
            emptyMessage="Sin datos de consultas aún."
            accent="bg-blue-50 text-blue-700 ring-blue-200 dark:bg-blue-50/20 dark:text-blue-200 dark:ring-blue-200/30"
          />
        </div>
      </CardContent>
    </Card>
  );
}
