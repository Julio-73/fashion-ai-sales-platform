"use client";

import { ArrowDown, ArrowUp, ShoppingCart, Target, TrendingUp, Users } from "lucide-react";

import { MetricCard } from "@/components/ui/metric-card";
import type { ExecutiveDashboardKpis } from "@/types/executive-dashboard";
import { cn } from "@/lib/utils";

type KpiStripProps = {
  kpis: ExecutiveDashboardKpis | null;
  isLoading: boolean;
};

const currencyFormatter = new Intl.NumberFormat("es-PE", {
  style: "currency",
  currency: "PEN",
  maximumFractionDigits: 0,
});

const numberFormatter = new Intl.NumberFormat("es-PE");

function trendFor(today: number, month: number) {
  if (month <= 0) return null;
  const pct = Math.round(((today - month) / month) * 100);
  if (pct === 0) return null;
  return {
    label: `${pct > 0 ? "+" : ""}${pct}% vs. mes`,
    positive: pct > 0,
  };
}

export function KpiStrip({ kpis, isLoading }: KpiStripProps) {
  if (isLoading || !kpis) {
    return (
      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="rounded-lg border bg-card p-5">
            <div className="h-3 w-24 animate-pulse rounded bg-muted" />
            <div className="mt-5 h-7 w-20 animate-pulse rounded bg-muted" />
            <div className="mt-4 h-3 w-16 animate-pulse rounded bg-muted" />
          </div>
        ))}
      </section>
    );
  }

  const salesTodayTrend = trendFor(kpis.sales_today, kpis.sales_month / 30);
  const conversionTone =
    kpis.conversion_rate_pct >= 25
      ? "text-emerald-700"
      : kpis.conversion_rate_pct >= 10
        ? "text-amber-700"
        : "text-rose-700";

  return (
    <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
      <MetricCard
        title="Ventas hoy"
        value={currencyFormatter.format(kpis.sales_today)}
        icon={TrendingUp}
        trend={salesTodayTrend?.label}
        delay={0}
        footer={
          <span className="text-xs text-muted-foreground">
            Acumulado del día en curso.
          </span>
        }
      />
      <MetricCard
        title="Ventas del mes"
        value={currencyFormatter.format(kpis.sales_month)}
        icon={ShoppingCart}
        delay={0.04}
        footer={
          <span className="text-xs text-muted-foreground">
            Ticket promedio: {currencyFormatter.format(kpis.average_ticket)}.
          </span>
        }
      />
      <MetricCard
        title="Clientes activos"
        value={numberFormatter.format(kpis.active_customers)}
        icon={Users}
        delay={0.08}
        footer={
          <span className="text-xs text-muted-foreground">
            {numberFormatter.format(kpis.vip_customers)} VIP · {numberFormatter.format(kpis.active_conversations)} conversaciones activas.
          </span>
        }
      />
      <MetricCard
        title="Leads abiertos"
        value={numberFormatter.format(kpis.leads_open)}
        icon={Target}
        delay={0.12}
        footer={
          <span className="text-xs text-muted-foreground">
            {numberFormatter.format(kpis.leads_won)} ganados · {numberFormatter.format(kpis.leads_lost)} perdidos.
          </span>
        }
      />
      <MetricCard
        title="Conversión"
        value={`${kpis.conversion_rate_pct.toFixed(1)}%`}
        icon={kpis.conversion_rate_pct >= 25 ? ArrowUp : ArrowDown}
        delay={0.16}
        footer={
          <span className={cn("text-xs font-medium", conversionTone)}>
            Sobre {numberFormatter.format(kpis.total_orders)} pedidos totales.
          </span>
        }
      />
    </section>
  );
}
