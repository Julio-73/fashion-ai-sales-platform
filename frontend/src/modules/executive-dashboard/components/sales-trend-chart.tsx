"use client";

import { useMemo, useState } from "react";
import { BarChart3, TrendingUp } from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { StatDelta } from "@/components/ui/stat";
import { cn, safeAverage, safeNumber, safeSum } from "@/lib/utils";
import type { ExecutiveDashboardDailyTrend } from "@/types/executive-dashboard";

type SalesTrendChartProps = {
  data: ExecutiveDashboardDailyTrend[];
  isLoading: boolean;
};

const currencyFormatter = new Intl.NumberFormat("es-PE", {
  style: "currency",
  currency: "PEN",
  maximumFractionDigits: 0
});

function shortDate(iso: string) {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleDateString("es-PE", { day: "2-digit", month: "short" });
}

export function SalesTrendChart({ data, isLoading }: SalesTrendChartProps) {
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);

  const summary = useMemo(() => {
    const safeRevenue = data.map((item) => safeNumber(item.revenue, 0));
    if (safeRevenue.length === 0) {
      return { total: 0, average: 0, peak: 0, peakDate: null as string | null };
    }
    const total = safeSum(safeRevenue, 0);
    const average = safeAverage(safeRevenue, 0);
    let peak = 0;
    let peakDate: string | null = null;
    for (let i = 0; i < data.length; i += 1) {
      const revenue = safeRevenue[i];
      if (revenue > peak) {
        peak = revenue;
        peakDate = data[i]?.date ?? null;
      }
    }
    return { total, average, peak, peakDate };
  }, [data]);

  const trend = useMemo(() => {
    if (data.length < 2) return null;
    const first = safeNumber(data[0]?.revenue, 0);
    const last = safeNumber(data[data.length - 1]?.revenue, 0);
    if (first <= 0) return null;
    const pct = Math.round(((last - first) / first) * 100);
    if (pct === 0) return null;
    return {
      value: `${pct > 0 ? "+" : ""}${pct}%`,
      direction: (pct > 0 ? "up" : "down") as "up" | "down"
    };
  }, [data]);

  const maxRevenue = useMemo(() => {
    if (data.length === 0) return 0;
    return data.reduce(
      (acc, item) => Math.max(acc, safeNumber(item.revenue, 0)),
      0
    );
  }, [data]);

  return (
    <Card variant="elevated">
      <CardContent>
        <div className="mb-5 flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-semibold tracking-tight">
                Tendencia de ventas diarias
              </h3>
              {trend ? (
                <StatDelta
                  value={trend.value}
                  direction={trend.direction}
                  size="sm"
                />
              ) : null}
            </div>
            <p className="mt-0.5 text-xs text-muted-foreground">
              Ingresos y pedidos en los últimos {data.length || 30} días.
            </p>
          </div>
          {hoverIndex !== null && data[hoverIndex] ? (
            <div className="hidden text-right text-xs text-muted-foreground sm:block">
              <p className="font-semibold text-foreground">
                {currencyFormatter.format(
                  safeNumber(data[hoverIndex].revenue, 0)
                )}
              </p>
              <p>
                {data[hoverIndex].orders} pedidos ·{" "}
                {shortDate(data[hoverIndex].date)}
              </p>
            </div>
          ) : null}
        </div>

        {isLoading ? (
          <div className="grid h-56 grid-cols-12 items-end gap-1.5">
            {Array.from({ length: 12 }).map((_, i) => (
              <Skeleton key={i} className="h-full w-full" />
            ))}
          </div>
        ) : data.length === 0 ? (
          <div className="flex h-56 items-center justify-center rounded-xl border border-dashed bg-muted/30 text-sm text-muted-foreground">
            Sin datos de ventas en los últimos 30 días.
          </div>
        ) : (
          <>
            <div className="relative h-56">
              <div className="absolute inset-0 flex items-end gap-1 overflow-hidden">
                {data.map((item, index) => {
                  const revenue = safeNumber(item.revenue, 0);
                  const pct =
                    maxRevenue > 0 ? (revenue / maxRevenue) * 100 : 0;
                  const safePct = Number.isFinite(pct) ? Math.max(pct, 2) : 2;
                  const isHover = hoverIndex === index;
                  return (
                    <div
                      key={item.date}
                      className="group relative flex h-full flex-1 flex-col justify-end"
                      onMouseEnter={() => setHoverIndex(index)}
                      onMouseLeave={() =>
                        setHoverIndex((current) =>
                          current === index ? null : current
                        )
                      }
                    >
                      <div
                        className={cn(
                          "w-full rounded-t-sm transition-all duration-300",
                          isHover
                            ? "bg-primary shadow-md"
                            : "bg-primary/60 group-hover:bg-primary/80"
                        )}
                        style={{ height: `${safePct}%` }}
                        title={`${shortDate(item.date)} · ${currencyFormatter.format(revenue)} · ${item.orders} pedidos`}
                      />
                    </div>
                  );
                })}
              </div>
            </div>
            <div className="mt-3 flex items-center justify-between text-[10px] text-muted-foreground">
              <span>{shortDate(data[0].date)}</span>
              <span>
                {shortDate(data[Math.floor(data.length / 2)].date)}
              </span>
              <span>{shortDate(data[data.length - 1].date)}</span>
            </div>
          </>
        )}

        <div className="mt-5 grid grid-cols-3 gap-3 border-t pt-4 text-xs">
          <div>
            <div className="flex items-center gap-1.5 text-muted-foreground">
              <BarChart3 className="h-3 w-3" aria-hidden="true" />
              <p>Promedio diario</p>
            </div>
            <p className="mt-1 text-sm font-semibold text-foreground">
              {currencyFormatter.format(summary.average)}
            </p>
          </div>
          <div>
            <div className="flex items-center gap-1.5 text-muted-foreground">
              <TrendingUp className="h-3 w-3" aria-hidden="true" />
              <p>Pico</p>
            </div>
            <p className="mt-1 text-sm font-semibold text-foreground">
              {currencyFormatter.format(summary.peak)}
            </p>
            <p className="text-[10px] text-muted-foreground">
              {summary.peakDate ? shortDate(summary.peakDate) : "—"}
            </p>
          </div>
          <div>
            <div className="flex items-center gap-1.5 text-muted-foreground">
              <span className="h-1.5 w-1.5 rounded-full bg-primary" />
              <p>Periodo</p>
            </div>
            <p className="mt-1 text-sm font-semibold text-foreground">
              {data.length} días
            </p>
            <p className="text-[10px] text-muted-foreground">
              Total: {currencyFormatter.format(summary.total)}
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
