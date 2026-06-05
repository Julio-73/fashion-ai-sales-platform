"use client";

import { Award, Eye, LineChart, ShoppingBag } from "lucide-react";
import type { LucideIcon } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import type { ExecutiveDashboardTopProducts } from "@/types/executive-dashboard";

type TopProductsProps = {
  data: ExecutiveDashboardTopProducts | null;
  isLoading: boolean;
};

const currencyFormatter = new Intl.NumberFormat("es-PE", {
  style: "currency",
  currency: "PEN",
  maximumFractionDigits: 0,
});

const numberFormatter = new Intl.NumberFormat("es-PE");

type ProductColumnProps = {
  title: string;
  icon: LucideIcon;
  items: Array<{ name: string; primary: string; secondary: string }>;
  isLoading: boolean;
  emptyMessage: string;
  accent: string;
};

function ProductColumn({ title, icon: Icon, items, isLoading, emptyMessage, accent }: ProductColumnProps) {
  return (
    <div className="rounded-lg border bg-background p-4">
      <div className="mb-3 flex items-center gap-2">
        <div className={`flex h-7 w-7 items-center justify-center rounded-md ${accent}`}>
          <Icon className="h-3.5 w-3.5" />
        </div>
        <p className="text-sm font-semibold text-foreground">{title}</p>
        <span className="ml-auto rounded-full bg-secondary px-2 py-0.5 text-[11px] font-medium text-muted-foreground">
          {items.length}
        </span>
      </div>
      {isLoading ? (
        <div className="space-y-2">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-8 w-full" />
          ))}
        </div>
      ) : items.length === 0 ? (
        <p className="py-4 text-center text-xs text-muted-foreground">{emptyMessage}</p>
      ) : (
        <ul className="space-y-2">
          {items.slice(0, 5).map((item, index) => (
            <li
              key={`${item.name}-${index}`}
              className="flex items-center justify-between gap-2 rounded-md border bg-card px-3 py-2"
            >
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium text-foreground">{item.name}</p>
                <p className="text-[11px] text-muted-foreground">{item.secondary}</p>
              </div>
              <span className="shrink-0 rounded-md bg-secondary px-2 py-0.5 text-[11px] font-mono font-semibold text-foreground">
                {item.primary}
              </span>
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
    secondary: `${currencyFormatter.format(p.revenue)} en ventas`,
  }));
  const mostProfitable = (data?.most_profitable ?? []).map((p) => ({
    name: p.name,
    primary: currencyFormatter.format(p.revenue),
    secondary: `${numberFormatter.format(p.units_sold)} unidades`,
  }));
  const mostConsulted = (data?.most_consulted ?? []).map((p) => ({
    name: p.name,
    primary: numberFormatter.format(p.mentions),
    secondary: "Consultas en conversaciones",
  }));

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10 text-primary">
            <LineChart className="h-4 w-4" />
          </div>
          <div>
            <CardTitle className="text-sm">Productos destacados</CardTitle>
            <p className="text-xs text-muted-foreground">
              Lo más vendido, rentable y consultado por tus clientes.
            </p>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid gap-4 lg:grid-cols-3">
          <ProductColumn
            title="Más vendidos"
            icon={ShoppingBag}
            items={mostSold}
            isLoading={isLoading}
            emptyMessage="Aún no hay ventas registradas."
            accent="bg-emerald-50 text-emerald-700"
          />
          <ProductColumn
            title="Más rentables"
            icon={Award}
            items={mostProfitable}
            isLoading={isLoading}
            emptyMessage="Aún no hay ingresos registrados."
            accent="bg-amber-50 text-amber-700"
          />
          <ProductColumn
            title="Más consultados"
            icon={Eye}
            items={mostConsulted}
            isLoading={isLoading}
            emptyMessage="Sin datos de consultas aún."
            accent="bg-blue-50 text-blue-700"
          />
        </div>
      </CardContent>
    </Card>
  );
}
