"use client";

import { Calendar, LineChart, Target } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import type {
  ExecutiveDashboardForecast,
  ExecutiveDashboardForecastConfidence
} from "@/types/executive-dashboard";
import { cn } from "@/lib/utils";

type SalesForecastProps = {
  forecast: ExecutiveDashboardForecast | null;
  isLoading: boolean;
};

const currencyFormatter = new Intl.NumberFormat("es-PE", {
  style: "currency",
  currency: "PEN",
  maximumFractionDigits: 0,
});

const confidenceTone: Record<ExecutiveDashboardForecastConfidence, { label: string; className: string; dot: string }> = {
  high: {
    label: "Alta",
    className: "bg-emerald-50 text-emerald-700 ring-emerald-200",
    dot: "bg-emerald-500",
  },
  medium: {
    label: "Media",
    className: "bg-amber-50 text-amber-700 ring-amber-200",
    dot: "bg-amber-500",
  },
  low: {
    label: "Baja",
    className: "bg-rose-50 text-rose-700 ring-rose-200",
    dot: "bg-rose-500",
  },
};

type ForecastCardProps = {
  title: string;
  icon: typeof LineChart;
  period: ExecutiveDashboardForecast["monthly"];
};

function ForecastCard({ title, icon: Icon, period }: ForecastCardProps) {
  const tone = confidenceTone[period.confidence];
  return (
    <div className="relative overflow-hidden rounded-lg border bg-gradient-to-br from-primary/5 via-card to-card p-5">
      <div className="flex items-center gap-2">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10 text-primary">
          <Icon className="h-4 w-4" />
        </div>
        <p className="text-sm font-semibold text-foreground">{title}</p>
        <span
          className={cn(
            "ml-auto inline-flex items-center gap-1.5 rounded-md px-2 py-0.5 text-[11px] font-medium ring-1",
            tone.className
          )}
        >
          <span className={cn("h-1.5 w-1.5 rounded-full", tone.dot)} />
          Confianza {tone.label}
        </span>
      </div>
      <p className="mt-4 text-3xl font-semibold tracking-normal text-foreground">
        {currencyFormatter.format(period.projected_revenue)}
      </p>
      <p className="mt-1 text-xs text-muted-foreground">
        Basado en {period.sample_size} muestras.
      </p>
      <p className="mt-3 border-t pt-3 text-xs leading-5 text-muted-foreground">
        {period.basis}
      </p>
    </div>
  );
}

export function SalesForecast({ forecast, isLoading }: SalesForecastProps) {
  if (isLoading || !forecast) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Proyecciones de ventas</CardTitle>
          <p className="text-xs text-muted-foreground">
            Estimaciones generadas a partir del histórico reciente.
          </p>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 lg:grid-cols-2">
            <Skeleton className="h-44" />
            <Skeleton className="h-44" />
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10 text-primary">
            <LineChart className="h-4 w-4" />
          </div>
          <div>
            <CardTitle className="text-sm">Proyecciones de ventas</CardTitle>
            <p className="text-xs text-muted-foreground">
              Estimaciones generadas a partir del histórico reciente.
            </p>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid gap-4 lg:grid-cols-2">
          <ForecastCard title="Proyección mensual" icon={Calendar} period={forecast.monthly} />
          <ForecastCard title="Proyección trimestral" icon={Target} period={forecast.quarterly} />
        </div>
      </CardContent>
    </Card>
  );
}
