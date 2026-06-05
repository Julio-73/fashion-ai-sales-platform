"use client";

import { TrendingUp } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import type { ExecutiveDashboardFunnelStage, ExecutiveDashboardPipeline } from "@/types/executive-dashboard";
import { cn } from "@/lib/utils";

type PipelineFunnelProps = {
  pipeline: ExecutiveDashboardPipeline | null;
  isLoading: boolean;
};

const currencyFormatter = new Intl.NumberFormat("es-PE", {
  style: "currency",
  currency: "PEN",
  maximumFractionDigits: 0,
});

const numberFormatter = new Intl.NumberFormat("es-PE");

function stageBgTint(color: string) {
  if (color.startsWith("#")) return undefined;
  return color;
}

export function PipelineFunnel({ pipeline, isLoading }: PipelineFunnelProps) {
  if (isLoading || !pipeline) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Embudo del pipeline</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-3 md:grid-cols-2">
            {Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} className="h-20" />
            ))}
          </div>
          <div className="mt-6 space-y-3">
            {Array.from({ length: 7 }).map((_, i) => (
              <Skeleton key={i} className="h-10" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  const stages: ExecutiveDashboardFunnelStage[] = [...pipeline.funnel].sort(
    (a, b) => a.order - b.order
  );
  const maxCount = stages.reduce((acc, stage) => Math.max(acc, stage.count), 0);

  const summaryCards = [
    {
      label: "Abiertos",
      value: numberFormatter.format(pipeline.open_deals),
      footer: currencyFormatter.format(pipeline.total_value),
    },
    {
      label: "Valor ponderado",
      value: currencyFormatter.format(pipeline.weighted_value),
      footer: "Probabilidad aplicada",
    },
    {
      label: "Ganados",
      value: numberFormatter.format(pipeline.won_deals),
      footer: currencyFormatter.format(pipeline.won_value),
    },
    {
      label: "Conversión",
      value: `${pipeline.conversion_pct.toFixed(1)}%`,
      footer: `${pipeline.average_time_to_close_days} días cierre prom.`,
    },
  ];

  return (
    <Card>
      <CardHeader>
        <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <CardTitle className="text-sm">Embudo del pipeline</CardTitle>
            <p className="mt-1 text-xs text-muted-foreground">
              Distribución de deals abiertos por etapa del pipeline comercial.
            </p>
          </div>
          <div className="inline-flex items-center gap-1 rounded-md bg-emerald-50 px-2 py-1 text-xs font-medium text-emerald-700">
            <TrendingUp className="h-3.5 w-3.5" />
            Conversión {pipeline.conversion_pct.toFixed(1)}%
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {summaryCards.map((card) => (
            <div key={card.label} className="rounded-lg border bg-secondary/40 p-3">
              <p className="text-[11px] uppercase tracking-wide text-muted-foreground">
                {card.label}
              </p>
              <p className="mt-1 text-lg font-semibold text-foreground">{card.value}</p>
              <p className="text-xs text-muted-foreground">{card.footer}</p>
            </div>
          ))}
        </div>

        <div className="mt-6 space-y-3">
          {stages.length === 0 ? (
            <p className="text-sm text-muted-foreground">Sin etapas registradas.</p>
          ) : (
            stages.map((stage) => {
              const widthPct = maxCount > 0 ? (stage.count / maxCount) * 100 : 0;
              const tint = stageBgTint(stage.color);
              return (
                <div key={stage.stage} className="grid gap-2 sm:grid-cols-[180px_1fr_auto] sm:items-center">
                  <div className="flex items-center gap-2">
                    <span
                      className={cn(
                        "h-2.5 w-2.5 shrink-0 rounded-full ring-2 ring-background",
                        tint ?? "bg-primary"
                      )}
                      style={tint ? { backgroundColor: tint } : undefined}
                    />
                    <span className="text-sm font-medium text-foreground">{stage.label}</span>
                  </div>
                  <div className="relative h-3 overflow-hidden rounded-full bg-muted">
                    <div
                      className="absolute inset-y-0 left-0 rounded-full transition-all duration-500"
                      style={{
                        width: `${Math.max(widthPct, 2)}%`,
                        backgroundColor: tint ?? "hsl(var(--primary))",
                      }}
                    />
                  </div>
                  <div className="flex items-center gap-3 text-xs sm:justify-end">
                    <span className="rounded-md bg-secondary px-2 py-1 font-semibold text-foreground">
                      {numberFormatter.format(stage.count)}
                    </span>
                    <span className="font-mono text-muted-foreground">
                      {currencyFormatter.format(stage.value)}
                    </span>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </CardContent>
    </Card>
  );
}
