"use client";

import { AlertCircle, RefreshCcw } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { ApiError } from "@/services/api-client";
import { useAuthStore } from "@/store/auth-store";
import type { ExecutiveDashboardResponse } from "@/types/executive-dashboard";
import { getExecutiveDashboard } from "@/modules/executive-dashboard/services/executive-dashboard-api";

import { AiRecommendationsPanel } from "./ai-recommendations-panel";
import { ExecutiveAlerts } from "./executive-alerts";
import { KpiStrip } from "./kpi-strip";
import { PipelineFunnel } from "./pipeline-funnel";
import { SalesForecast } from "./sales-forecast";
import { SalesTrendChart } from "./sales-trend-chart";
import { TopCustomersTable } from "./top-customers-table";
import { TopProducts } from "./top-products";

export function ExecutiveDashboardWorkspace() {
  const { accessToken, refreshToken, user, refreshSession, logout } = useAuthStore();
  const [data, setData] = useState<ExecutiveDashboardResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const activeRef = useRef(true);

  const load = useCallback(
    async (retried = false) => {
      if (!accessToken) return;
      setIsLoading(true);
      setError(null);
      try {
        const response = await getExecutiveDashboard(accessToken);
        if (!activeRef.current) return;
        setData(response);
      } catch (err) {
        if (!activeRef.current) return;
        if (!retried && err instanceof ApiError && err.status === 401) {
          if (!refreshToken || !user) {
            await logout();
            return;
          }
          try {
            await refreshSession();
          } catch {
            await logout();
            return;
          }
          return;
        }
        setError("No se pudo cargar el dashboard ejecutivo. Verifica el backend y tu sesión.");
      } finally {
        if (activeRef.current) setIsLoading(false);
      }
    },
    [accessToken, refreshToken, user, refreshSession, logout]
  );

  useEffect(() => {
    activeRef.current = true;
    load();
    return () => {
      activeRef.current = false;
    };
  }, [load]);

  useEffect(() => {
    function handleFocus() {
      load();
    }
    window.addEventListener("focus", handleFocus);
    return () => window.removeEventListener("focus", handleFocus);
  }, [load]);

  if (error && !data) {
    return (
      <Card>
        <CardContent className="flex flex-col items-center gap-4 py-10 text-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-rose-50 text-rose-700">
            <AlertCircle className="h-5 w-5" />
          </div>
          <div>
            <p className="text-sm font-semibold text-foreground">No se pudo cargar el dashboard</p>
            <p className="mt-1 max-w-md text-xs text-muted-foreground">{error}</p>
          </div>
          <Button type="button" variant="default" size="sm" onClick={() => load()}>
            <RefreshCcw className="h-3.5 w-3.5" />
            Reintentar
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="grid gap-6">
      <KpiStrip kpis={data?.kpis ?? null} isLoading={isLoading} />

      <div className="grid gap-6 lg:grid-cols-[1.6fr_1fr]">
        <SalesTrendChart data={data?.sales_trend.daily ?? []} isLoading={isLoading} />
        <SalesForecast forecast={data?.forecast ?? null} isLoading={isLoading} />
      </div>

      <AiRecommendationsPanel
        recommendations={data?.ai_recommendations ?? []}
        isLoading={isLoading}
      />

      <PipelineFunnel pipeline={data?.pipeline ?? null} isLoading={isLoading} />

      <TopCustomersTable customers={data?.top_customers ?? []} isLoading={isLoading} />

      <TopProducts data={data?.top_products ?? null} isLoading={isLoading} />

      <ExecutiveAlerts alerts={data?.alerts ?? null} isLoading={isLoading} />

      {data ? (
        <p className="text-right text-[10px] text-muted-foreground">
          Actualizado {new Date(data.generated_at).toLocaleString("es-PE")} · calculado en {data.metadata.computed_in_ms} ms.
        </p>
      ) : null}
    </div>
  );
}
