"use client";

import { ArrowDown, ArrowUp, ShoppingCart, Target, TrendingUp, Users } from "lucide-react";

import { MetricCard } from "@/components/ui/metric-card";
import { DashboardSkeleton } from "@/components/ui/skeleton";
import { StatDelta } from "@/components/ui/stat";
import type { ExecutiveDashboardKpis } from "@/types/executive-dashboard";

type KpiStripProps = {
  kpis: ExecutiveDashboardKpis | null;
  isLoading: boolean;
};

const currencyFormatter = new Intl.NumberFormat("es-PE", {
  style: "currency",
  currency: "PEN",
  maximumFractionDigits: 0
});

const numberFormatter = new Intl.NumberFormat("es-PE");

function trendFor(today: number, month: number) {
  if (month <= 0) return null;
  const pct = Math.round(((today - month) / month) * 100);
  if (pct === 0) return null;
  return {
    label: `${pct > 0 ? "+" : ""}${pct}%`,
    direction: (pct > 0 ? "up" : "down") as "up" | "down"
  };
}

export function KpiStrip({ kpis, isLoading }: KpiStripProps) {
  if (isLoading || !kpis) {
    return <DashboardSkeleton count={5} />;
  }

  const salesTodayTrend = trendFor(kpis.sales_today, kpis.sales_month / 30);
  const conversionDirection: "up" | "down" | "flat" =
    kpis.conversion_rate_pct >= 25
      ? "up"
      : kpis.conversion_rate_pct >= 10
        ? "flat"
        : "down";

  return (
    <section
      aria-label="KPIs principales"
      className="grid gap-4 md:grid-cols-2 xl:grid-cols-5"
    >
      <MetricCard
        title="Ventas hoy"
        value={currencyFormatter.format(kpis.sales_today)}
        icon={TrendingUp}
        iconTone="primary"
        trend={salesTodayTrend?.label}
        trendDirection={salesTodayTrend?.direction}
        delay={0}
        description="Acumulado del día en curso."
      />
      <MetricCard
        title="Ventas del mes"
        value={currencyFormatter.format(kpis.sales_month)}
        icon={ShoppingCart}
        iconTone="purple"
        delay={0.04}
        description={`Ticket promedio: ${currencyFormatter.format(kpis.average_ticket)}.`}
      />
      <MetricCard
        title="Clientes activos"
        value={numberFormatter.format(kpis.active_customers)}
        icon={Users}
        iconTone="info"
        delay={0.08}
        description={`${numberFormatter.format(kpis.vip_customers)} VIP · ${numberFormatter.format(kpis.active_conversations)} conversaciones activas.`}
      />
      <MetricCard
        title="Leads abiertos"
        value={numberFormatter.format(kpis.leads_open)}
        icon={Target}
        iconTone="warning"
        delay={0.12}
        description={`${numberFormatter.format(kpis.leads_won)} ganados · ${numberFormatter.format(kpis.leads_lost)} perdidos.`}
      />
      <MetricCard
        title="Conversión"
        value={`${kpis.conversion_rate_pct.toFixed(1)}%`}
        icon={conversionDirection === "down" ? ArrowDown : ArrowUp}
        iconTone={conversionDirection === "up" ? "success" : conversionDirection === "down" ? "destructive" : "warning"}
        delay={0.16}
        description={
          <span className="inline-flex items-center gap-1.5">
            Sobre {numberFormatter.format(kpis.total_orders)} pedidos totales.
            <StatDelta
              value={conversionDirection === "up" ? "Sano" : conversionDirection === "flat" ? "Estable" : "Bajo"}
              direction={conversionDirection}
              size="sm"
            />
          </span>
        }
      />
    </section>
  );
}
