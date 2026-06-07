"use client";

import { Calendar, LineChart, Sparkles, Target } from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { StatusPill } from "@/components/ui/status-pill";
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
  maximumFractionDigits: 0
});

const confidenceTone: Record<
  ExecutiveDashboardForecastConfidence,
  "success" | "warning" | "destructive"
> = {
  high: "success",
  medium: "warning",
  low: "destructive"
};

const confidenceLabel: Record<ExecutiveDashboardForecastConfidence, string> = {
  high: "Alta",
  medium: "Media",
  low: "Baja"
};

type ForecastCardProps = {
  title: string;
  icon: typeof LineChart;
  period: ExecutiveDashboardForecast["monthly"];
};

function ForecastCard({ title, icon: Icon, period }: ForecastCardProps) {
  return (
    <div className="group relative overflow-hidden rounded-xl border bg-gradient-to-br from-card via-card to-primary-50/40 p-5 transition-all hover:shadow-md dark:to-primary-50/5">
      <div
        aria-hidden="true"
        className="pointer-events-none absolute -right-10 -top-10 h-32 w-32 rounded-full bg-primary-100/40 blur-2xl dark:bg-primary-300/5"
      />
      <div className="relative">
        <div className="flex items-center gap-2">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary-50 text-primary ring-1 ring-primary-200/60 dark:bg-primary-50/20 dark:text-primary-300 dark:ring-primary-300/30">
            <Icon className="h-4 w-4" />
          </div>
          <p className="text-sm font-semibold tracking-tight text-foreground">
            {title}
          </p>
          <StatusPill tone={confidenceTone[period.confidence]} dot className="ml-auto">
            Confianza {confidenceLabel[period.confidence]}
          </StatusPill>
        </div>
        <p className="mt-5 text-3xl font-semibold tracking-tight text-foreground">
          {currencyFormatter.format(period.projected_revenue)}
        </p>
        <p className="mt-1 text-xs text-muted-foreground">
          Basado en {period.sample_size} muestras.
        </p>
        <p className="mt-3 border-t pt-3 text-xs leading-5 text-muted-foreground">
          {period.basis}
        </p>
      </div>
    </div>
  );
}

export function SalesForecast({ forecast, isLoading }: SalesForecastProps) {
  if (isLoading || !forecast) {
    return (
      <Card variant="elevated">
        <CardContent>
          <div className="mb-5 flex items-center gap-2">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary-50 text-primary">
              <LineChart className="h-4 w-4" />
            </div>
            <div>
              <h3 className="text-sm font-semibold tracking-tight">
                Proyecciones de ventas
              </h3>
              <p className="text-xs text-muted-foreground">
                Estimaciones generadas a partir del histórico reciente.
              </p>
            </div>
          </div>
          <div className="grid gap-4 lg:grid-cols-2">
            <Skeleton className="h-44 rounded-xl" />
            <Skeleton className="h-44 rounded-xl" />
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card variant="elevated">
      <CardContent>
        <div className="mb-5 flex items-center gap-2">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary-50 text-primary ring-1 ring-primary-200/60">
            <Sparkles className="h-4 w-4" />
          </div>
          <div>
            <h3 className="text-sm font-semibold tracking-tight">
              Proyecciones de ventas
            </h3>
            <p className="text-xs text-muted-foreground">
              Estimaciones generadas a partir del histórico reciente.
            </p>
          </div>
        </div>
        <div className="grid gap-4 lg:grid-cols-2">
          <ForecastCard
            title="Proyección mensual"
            icon={Calendar}
            period={forecast.monthly}
          />
          <ForecastCard
            title="Proyección trimestral"
            icon={Target}
            period={forecast.quarterly}
          />
        </div>
      </CardContent>
    </Card>
  );
}
