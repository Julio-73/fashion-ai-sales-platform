"use client";

import { useCallback, useEffect, useState } from "react";
import {
  AlertTriangle,
  Bell,
  CircleDashed,
  Flame,
  ListChecks,
  Loader2,
  Package,
  RefreshCw,
  ShoppingBag,
  Snowflake
} from "lucide-react";

import { AppShell } from "@/components/layout/app-shell";
import { DashboardContent } from "@/components/layout/dashboard-content";
import { PageHeader } from "@/components/layout/page-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { MetricCard } from "@/components/ui/metric-card";
import { StatusPill } from "@/components/ui/status-pill";
import { EmptyState } from "@/components/feedback/empty-state";
import { useAuthStore } from "@/store/auth-store";
import {
  fetchEvents,
  fetchMetrics,
  runEngine
} from "@/services/automation.service";
import { cn } from "@/lib/utils";
import type {
  AutomationEvent,
  AutomationMetrics
} from "@/types/automation";

const SEVERITY_TONE: Record<string, "destructive" | "warning" | "info"> = {
  critical: "destructive",
  warning: "warning",
  info: "info"
};

const SEVERITY_LABEL: Record<string, string> = {
  critical: "Crítica",
  warning: "Advertencia",
  info: "Info"
};

function formatDateTime(value: string | null): string {
  if (!value) return "—";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return "—";
  return d.toLocaleString("es-ES", {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit"
  });
}

function EventCard({ ev }: { ev: AutomationEvent }) {
  const tone = SEVERITY_TONE[ev.severity] || "info";
  return (
    <Card
      className={cn(
        "transition-all hover:-translate-y-px hover:shadow-md",
        ev.severity === "critical" && "ring-1 ring-destructive/30",
        ev.severity === "warning" && "ring-1 ring-warning-200"
      )}
    >
      <CardContent className="space-y-1.5 p-3">
        <div className="flex items-center justify-between gap-2">
          <span className="truncate text-sm font-semibold tracking-tight text-foreground">
            {ev.event_type}
          </span>
          <StatusPill tone={tone} size="sm" dot>
            {SEVERITY_LABEL[ev.severity] || ev.severity}
          </StatusPill>
        </div>
        <p className="text-xs text-muted-foreground">
          Regla <span className="font-medium text-foreground">{ev.rule_key}</span>
          {" · "}
          {formatDateTime(ev.created_at)}
        </p>
        {ev.payload && Object.keys(ev.payload).length > 0 ? (
          <pre className="max-h-32 overflow-auto rounded-md border border-border bg-muted/40 p-2 text-[10px] text-muted-foreground">
            {JSON.stringify(ev.payload, null, 2)}
          </pre>
        ) : null}
      </CardContent>
    </Card>
  );
}

export default function AlertsPage() {
  const { accessToken, refreshSession } = useAuthStore();
  const [events, setEvents] = useState<AutomationEvent[]>([]);
  const [metrics, setMetrics] = useState<AutomationMetrics | null>(null);
  const [loading, setLoading] = useState(false);
  const [running, setRunning] = useState(false);
  const [severity, setSeverity] = useState<string>("");

  const runWithAuth = useCallback(
    async <T,>(fn: (token: string) => Promise<T>): Promise<T | null> => {
      if (!accessToken) return null;
      try {
        return await fn(accessToken);
      } catch (err) {
        if (
          err &&
          typeof err === "object" &&
          "status" in err &&
          (err as { status?: number }).status === 401
        ) {
          await refreshSession();
        }
        return null;
      }
    },
    [accessToken, refreshSession]
  );

  const reload = useCallback(async () => {
    if (!accessToken) return;
    setLoading(true);
    try {
      const [ev, m] = await Promise.all([
        runWithAuth((t) =>
          fetchEvents(t, {
            severity: severity || undefined,
            limit: 80
          })
        ),
        runWithAuth((t) => fetchMetrics(t))
      ]);
      if (ev) setEvents(ev);
      if (m) setMetrics(m);
    } finally {
      setLoading(false);
    }
  }, [accessToken, runWithAuth, severity]);

  useEffect(() => {
    reload();
  }, [reload]);

  const handleRun = useCallback(async () => {
    if (!accessToken) return;
    setRunning(true);
    try {
      await runWithAuth((t) => runEngine(t));
      reload();
    } finally {
      setRunning(false);
    }
  }, [accessToken, runWithAuth, reload]);

  return (
    <AppShell>
      <DashboardContent>
        <PageHeader
          eyebrow="Automatización"
          title="Alert Center"
          description="Leads calientes, leads fríos, negociaciones detenidas, clientes VIP inactivos, pedidos en riesgo e inventario crítico."
          breadcrumbs={[
            { label: "Workspace", href: "/dashboard" },
            { label: "Automatización" },
            { label: "Alert Center" }
          ]}
          status={
            (metrics?.alerts_critical ?? 0) > 0
              ? { label: `${metrics?.alerts_critical} críticas`, tone: "warning" }
              : { label: "Estable", tone: "success" }
          }
          actions={
            <Button onClick={handleRun} disabled={running}>
              {running ? (
                <Loader2 className="mr-1.5 h-4 w-4 animate-spin" />
              ) : (
                <RefreshCw className="mr-1.5 h-4 w-4" />
              )}
              Ejecutar motor
            </Button>
          }
        />

        <div className="flex flex-col gap-4">
          <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-3">
            <MetricCard
              title="Leads calientes"
              value={String(metrics?.tasks_pending ?? 0)}
              icon={Flame}
              iconTone="destructive"
              description="Activos en el centro de tareas"
            />
            <MetricCard
              title="Leads fríos"
              value={String(metrics?.tasks_overdue ?? 0)}
              icon={Snowflake}
              iconTone="info"
              description="Tareas vencidas"
            />
            <MetricCard
              title="Negociaciones detenidas"
              value={String(
                (metrics?.tasks_total ?? 0) - (metrics?.tasks_completed ?? 0)
              )}
              icon={CircleDashed}
              iconTone="warning"
              description="Abiertas en el motor"
            />
            <MetricCard
              title="Clientes VIP inactivos"
              value={String(metrics?.alerts_critical ?? 0)}
              icon={AlertTriangle}
              iconTone="destructive"
              description="Severidad crítica"
            />
            <MetricCard
              title="Pedidos en riesgo"
              value={String(metrics?.by_task_type?.order_risk ?? 0)}
              icon={ShoppingBag}
              iconTone="warning"
              description="Tareas activas"
            />
            <MetricCard
              title="Inventario crítico"
              value={String(metrics?.by_task_type?.inventory_check ?? 0)}
              icon={Package}
              iconTone="purple"
              description="Alertas generadas"
            />
          </div>

          <Card variant="elevated">
            <div className="flex flex-row items-center justify-between gap-2 border-b border-border px-4 py-3">
              <div className="flex items-center gap-2">
                <span className="flex h-7 w-7 items-center justify-center rounded-md bg-primary-50 text-primary">
                  <Bell className="h-3.5 w-3.5" aria-hidden="true" />
                </span>
                <h3 className="text-sm font-semibold tracking-tight text-foreground">
                  Eventos del motor
                </h3>
                <StatusPill tone="neutral" size="sm">
                  {events.length}
                </StatusPill>
              </div>
              <select
                value={severity}
                onChange={(e) => setSeverity(e.target.value)}
                className="h-8 rounded-md border border-input bg-background px-2 text-xs shadow-xs focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              >
                <option value="">Todas las severidades</option>
                <option value="critical">Crítica</option>
                <option value="warning">Advertencia</option>
                <option value="info">Info</option>
              </select>
            </div>
            <CardContent>
              {loading ? (
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <Loader2 className="h-3 w-3 animate-spin" /> Cargando…
                </div>
              ) : events.length === 0 ? (
                <EmptyState
                  icon={Bell}
                  title="No hay eventos recientes"
                  description="Ejecuta el motor para generar nuevas alertas y eventos."
                />
              ) : (
                <div className="grid grid-cols-1 gap-2 md:grid-cols-2 xl:grid-cols-3">
                  {events.map((ev) => (
                    <EventCard key={ev.id} ev={ev} />
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-4">
            <MetricCard
              title="Reglas activas"
              value={`${metrics?.rules_enabled ?? 0}/${metrics?.rules_total ?? 0}`}
              icon={ListChecks}
              iconTone="primary"
              description="Disponibles en /automation/rules"
            />
            <MetricCard
              title="Ejecuciones"
              value={String(metrics?.automation_executions ?? 0)}
              icon={RefreshCw}
              iconTone="info"
              description="Eventos totales"
            />
            <MetricCard
              title="Leads recuperados"
              value={String(metrics?.leads_recovered ?? 0)}
              icon={Flame}
              iconTone="success"
              description="Tareas cerradas"
            />
            <MetricCard
              title="Cierres tras automatización"
              value={String(metrics?.won_after_automation ?? 0)}
              icon={ShoppingBag}
              iconTone="purple"
              description="Tareas propuestas / llamadas / reuniones"
            />
          </div>
        </div>
      </DashboardContent>
    </AppShell>
  );
}
