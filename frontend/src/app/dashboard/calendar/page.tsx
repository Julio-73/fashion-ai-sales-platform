"use client";

import { useEffect, useState } from "react";
import { CalendarDays, Loader2 } from "lucide-react";

import { AppShell } from "@/components/layout/app-shell";
import { DashboardContent } from "@/components/layout/dashboard-content";
import { PageHeader } from "@/components/layout/page-header";
import { Card, CardContent } from "@/components/ui/card";
import { StatusBadge } from "@/components/ui/status-badge";
import { useAuthStore } from "@/store/auth-store";
import { fetchCalendar } from "@/services/automation.service";
import type {
  AutomationCalendarEntry,
  AutomationCalendarView
} from "@/types/automation";

const PRIORITY_TONE: Record<string, "success" | "warning" | "neutral"> = {
  critical: "warning",
  high: "warning",
  medium: "neutral",
  low: "neutral"
};

const PRIORITY_LABEL: Record<string, string> = {
  critical: "Crítica",
  high: "Alta",
  medium: "Media",
  low: "Baja"
};

const TYPE_LABEL: Record<string, string> = {
  follow_up: "Seguimiento",
  call: "Llamada",
  proposal: "Propuesta",
  meeting: "Reunión",
  recovery: "Recuperación",
  alert: "Alerta",
  win_log: "Cierre ganado",
  loss_log: "Cierre perdido"
};

function groupByDay(entries: AutomationCalendarEntry[]): Record<string, AutomationCalendarEntry[]> {
  return entries.reduce<Record<string, AutomationCalendarEntry[]>>((acc, e) => {
    const d = new Date(e.due_date);
    const key = d.toLocaleDateString("es-ES", {
      weekday: "long",
      day: "2-digit",
      month: "long"
    });
    acc[key] = acc[key] || [];
    acc[key].push(e);
    return acc;
  }, {});
}

export default function CalendarPage() {
  const { accessToken } = useAuthStore();
  const [view, setView] = useState<"day" | "week" | "month">("week");
  const [data, setData] = useState<AutomationCalendarView | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let cancelled = false;
    async function run() {
      if (!accessToken) return;
      setLoading(true);
      try {
        const v = await fetchCalendar(accessToken, { view });
        if (!cancelled) setData(v);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    run();
    return () => {
      cancelled = true;
    };
  }, [accessToken, view]);

  const grouped = data ? groupByDay(data.entries) : {};
  const total = data?.total ?? 0;

  return (
    <AppShell>
      <DashboardContent>
        <PageHeader
          eyebrow="Automatización"
          title="Calendario comercial"
          description="Seguimientos, llamadas, reuniones, cierres proyectados y vencimientos."
          breadcrumbs={[
            { label: "Workspace", href: "/dashboard" },
            { label: "Automatización" },
            { label: "Calendario" }
          ]}
        />
        <div className="flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1 rounded-lg border border-border bg-card p-0.5">
              {(["day", "week", "month"] as const).map((v) => (
                <button
                  key={v}
                  type="button"
                  onClick={() => setView(v)}
                  className={`rounded-md px-3 py-1.5 text-xs font-medium transition ${
                    view === v
                      ? "bg-primary text-primary-foreground shadow-xs"
                      : "text-muted-foreground hover:bg-muted hover:text-foreground"
                  }`}
                >
                  {v === "day" ? "Día" : v === "week" ? "Semana" : "Mes"}
                </button>
              ))}
            </div>
            <span className="text-xs text-muted-foreground">
              {total} entradas en la vista
            </span>
          </div>

          {loading ? (
            <p className="flex items-center gap-2 text-xs text-muted-foreground">
              <Loader2 className="h-3 w-3 animate-spin" /> Cargando…
            </p>
          ) : null}

          <div className="space-y-3">
            {Object.keys(grouped).length === 0 && !loading ? (
              <Card>
                <CardContent className="flex flex-col items-center gap-2 p-10 text-center">
                  <CalendarDays className="h-8 w-8 text-muted-foreground/40" />
                  <p className="text-sm font-medium text-foreground">
                    Sin entradas en el rango seleccionado
                  </p>
                  <p className="text-xs text-muted-foreground">
                    Las tareas se generan automáticamente a partir de las reglas
                    activas.
                  </p>
                </CardContent>
              </Card>
            ) : null}
            {Object.entries(grouped).map(([day, items]) => (
              <Card key={day}>
                <CardContent className="space-y-2 p-4">
                  <h3 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                    {day}
                  </h3>
                  <div className="divide-y divide-border">
                    {items.map((e) => (
                      <div
                        key={e.task_id}
                        className="flex flex-wrap items-center gap-2 py-2 text-sm"
                      >
                        <CalendarDays className="h-4 w-4 text-primary" />
                        <span className="font-medium text-foreground">
                          {e.title}
                        </span>
                        <span className="text-xs text-muted-foreground">
                          {new Date(e.due_date).toLocaleTimeString("es-ES", {
                            hour: "2-digit",
                            minute: "2-digit"
                          })}
                        </span>
                        <StatusBadge tone={PRIORITY_TONE[e.priority] || "neutral"}>
                          {PRIORITY_LABEL[e.priority] || e.priority}
                        </StatusBadge>
                        <span className="ml-auto text-[10px] uppercase tracking-wide text-muted-foreground">
                          {TYPE_LABEL[e.task_type] || e.task_type}
                        </span>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </DashboardContent>
    </AppShell>
  );
}
