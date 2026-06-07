"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  Calendar,
  CheckCircle2,
  CircleDashed,
  Clock,
  Filter,
  Inbox,
  ListChecks,
  Loader2,
  Play,
  RefreshCw,
  Search,
  Sparkles,
  X
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { MetricCard } from "@/components/ui/metric-card";
import { StatusBadge } from "@/components/ui/status-badge";
import { useAuthStore } from "@/store/auth-store";
import * as automationService from "@/services/automation.service";
import type {
  AutomationMetrics,
  AutomationTask,
  AutomationTaskBoard
} from "@/types/automation";

type View = "board" | "list" | "calendar" | "alerts";

const PRIORITY_TONE: Record<string, "success" | "warning" | "neutral"> = {
  critical: "warning",
  high: "warning",
  medium: "neutral",
  low: "neutral"
};

const STATUS_TONE: Record<string, "success" | "warning" | "neutral"> = {
  completed: "success",
  pending: "neutral",
  in_progress: "neutral",
  overdue: "warning",
  cancelled: "neutral"
};

const STATUS_LABEL: Record<string, string> = {
  pending: "Pendiente",
  in_progress: "En curso",
  completed: "Completada",
  cancelled: "Cancelada",
  overdue: "Vencida"
};

const PRIORITY_LABEL: Record<string, string> = {
  low: "Baja",
  medium: "Media",
  high: "Alta",
  critical: "Crítica"
};

const TYPE_LABEL: Record<string, string> = {
  follow_up: "Seguimiento",
  call: "Llamada",
  proposal: "Propuesta",
  meeting: "Reunión",
  recovery: "Recuperación",
  alert: "Alerta",
  win_log: "Cierre ganado",
  loss_log: "Cierre perdido",
  pipeline_event: "Evento pipeline",
  inventory_check: "Inventario",
  order_risk: "Riesgo de pedido"
};

function formatDate(value: string | null): string {
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

function TaskCard({
  task,
  onComplete,
  onCancel
}: {
  task: AutomationTask;
  onComplete: (id: string) => void;
  onCancel: (id: string) => void;
}) {
  return (
    <Card className="border-slate-200">
      <CardContent className="space-y-2 p-4">
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-semibold text-slate-900">
              {task.title}
            </p>
            <p className="mt-0.5 text-xs text-slate-500">
              {TYPE_LABEL[task.task_type] || task.task_type} · Vence{" "}
              {formatDate(task.due_date)}
            </p>
          </div>
          <StatusBadge tone={PRIORITY_TONE[task.priority] || "neutral"}>
            {PRIORITY_LABEL[task.priority] || task.priority}
          </StatusBadge>
        </div>
        {task.description ? (
          <p className="line-clamp-2 text-xs text-slate-600">
            {task.description}
          </p>
        ) : null}
        {task.ai_next_action ? (
          <div className="flex items-center gap-1.5 rounded-md bg-indigo-50 px-2 py-1.5 text-xs text-indigo-700">
            <Sparkles className="h-3.5 w-3.5" />
            <span className="line-clamp-1">{task.ai_next_action}</span>
            {typeof task.ai_score === "number" ? (
              <span className="ml-auto text-[10px] font-semibold uppercase tracking-wide">
                Score {task.ai_score}
              </span>
            ) : null}
          </div>
        ) : null}
        <div className="flex items-center gap-2 pt-1">
          <StatusBadge tone={STATUS_TONE[task.status] || "neutral"}>
            {STATUS_LABEL[task.status] || task.status}
          </StatusBadge>
          {task.status !== "completed" && task.status !== "cancelled" ? (
            <>
              <Button
                size="sm"
                variant="outline"
                className="h-7 text-xs"
                onClick={() => onComplete(task.id)}
              >
                <CheckCircle2 className="mr-1 h-3 w-3" /> Completar
              </Button>
              <Button
                size="sm"
                variant="ghost"
                className="h-7 text-xs text-slate-500"
                onClick={() => onCancel(task.id)}
              >
                <X className="mr-1 h-3 w-3" /> Cancelar
              </Button>
            </>
          ) : null}
        </div>
      </CardContent>
    </Card>
  );
}

function BoardView({
  board,
  onComplete,
  onCancel
}: {
  board: AutomationTaskBoard;
  onComplete: (id: string) => void;
  onCancel: (id: string) => void;
}) {
  return (
    <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-5">
      {board.columns.map((col) => (
        <div key={col.key} className="flex flex-col gap-2">
          <div className="flex items-center justify-between rounded-md bg-slate-100 px-3 py-2">
            <h3 className="text-xs font-semibold uppercase tracking-wide text-slate-700">
              {col.label}
            </h3>
            <span className="rounded-full bg-white px-2 py-0.5 text-[10px] font-semibold text-slate-700 ring-1 ring-slate-200">
              {col.count}
            </span>
          </div>
          <div className="flex max-h-[60vh] flex-col gap-2 overflow-y-auto pr-1">
            {col.tasks.length === 0 ? (
              <p className="rounded-md border border-dashed border-slate-200 px-3 py-6 text-center text-xs text-slate-400">
                Sin tareas
              </p>
            ) : (
              col.tasks.map((t) => (
                <TaskCard
                  key={t.id}
                  task={t}
                  onComplete={onComplete}
                  onCancel={onCancel}
                />
              ))
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

function ListView({
  tasks,
  onComplete,
  onCancel
}: {
  tasks: AutomationTask[];
  onComplete: (id: string) => void;
  onCancel: (id: string) => void;
}) {
  return (
    <Card>
      <CardContent className="p-0">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200 text-sm">
            <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
              <tr>
                <th className="px-3 py-2 text-left">Tarea</th>
                <th className="px-3 py-2 text-left">Tipo</th>
                <th className="px-3 py-2 text-left">Prioridad</th>
                <th className="px-3 py-2 text-left">Estado</th>
                <th className="px-3 py-2 text-left">Vence</th>
                <th className="px-3 py-2 text-left">IA</th>
                <th className="px-3 py-2 text-right">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 bg-white">
              {tasks.length === 0 ? (
                <tr>
                  <td
                    colSpan={7}
                    className="px-3 py-6 text-center text-xs text-slate-400"
                  >
                    No hay tareas
                  </td>
                </tr>
              ) : (
                tasks.map((t) => (
                  <tr key={t.id} className="hover:bg-slate-50">
                    <td className="max-w-[260px] truncate px-3 py-2 font-medium text-slate-800">
                      {t.title}
                    </td>
                    <td className="px-3 py-2 text-xs text-slate-600">
                      {TYPE_LABEL[t.task_type] || t.task_type}
                    </td>
                    <td className="px-3 py-2">
                      <StatusBadge tone={PRIORITY_TONE[t.priority] || "neutral"}>
                        {PRIORITY_LABEL[t.priority] || t.priority}
                      </StatusBadge>
                    </td>
                    <td className="px-3 py-2">
                      <StatusBadge tone={STATUS_TONE[t.status] || "neutral"}>
                        {STATUS_LABEL[t.status] || t.status}
                      </StatusBadge>
                    </td>
                    <td className="px-3 py-2 text-xs text-slate-600">
                      {formatDate(t.due_date)}
                    </td>
                    <td className="px-3 py-2 text-xs text-slate-600">
                      {t.ai_next_action
                        ? `${t.ai_next_action}${t.ai_score ? ` · ${t.ai_score}` : ""}`
                        : "—"}
                    </td>
                    <td className="px-3 py-2 text-right">
                      {t.status !== "completed" && t.status !== "cancelled" ? (
                        <div className="flex justify-end gap-1">
                          <Button
                            size="sm"
                            variant="outline"
                            className="h-7 text-xs"
                            onClick={() => onComplete(t.id)}
                          >
                            <CheckCircle2 className="mr-1 h-3 w-3" />
                            Hecho
                          </Button>
                          <Button
                            size="sm"
                            variant="ghost"
                            className="h-7 text-xs"
                            onClick={() => onCancel(t.id)}
                          >
                            Cancelar
                          </Button>
                        </div>
                      ) : null}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}

function CalendarView({
  entries,
  view,
  onChangeView
}: {
  entries: import("@/types/automation").AutomationCalendarEntry[];
  view: "day" | "week" | "month";
  onChangeView: (v: "day" | "week" | "month") => void;
}) {
  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        {(["day", "week", "month"] as const).map((v) => (
          <button
            type="button"
            key={v}
            onClick={() => onChangeView(v)}
            className={`rounded-md px-3 py-1.5 text-xs font-medium ${
              v === view
                ? "bg-indigo-600 text-white"
                : "bg-slate-100 text-slate-700 hover:bg-slate-200"
            }`}
          >
            {v === "day" ? "Día" : v === "week" ? "Semana" : "Mes"}
          </button>
        ))}
      </div>
      <Card>
        <CardContent className="p-0">
          <div className="divide-y divide-slate-100">
            {entries.length === 0 ? (
              <p className="px-4 py-8 text-center text-xs text-slate-400">
                Sin seguimientos programados
              </p>
            ) : (
              entries.map((e) => (
                <div
                  key={e.task_id}
                  className="flex items-center gap-3 px-4 py-2.5 text-sm"
                >
                  <Calendar className="h-4 w-4 text-indigo-500" />
                  <span className="font-medium text-slate-800">{e.title}</span>
                  <span className="text-xs text-slate-500">
                    {formatDate(e.due_date)}
                  </span>
                  <StatusBadge tone={PRIORITY_TONE[e.priority] || "neutral"}>
                    {PRIORITY_LABEL[e.priority] || e.priority}
                  </StatusBadge>
                  <span className="ml-auto text-[10px] uppercase tracking-wide text-slate-500">
                    {TYPE_LABEL[e.task_type] || e.task_type}
                  </span>
                </div>
              ))
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function AlertsView({
  metrics,
  onRun
}: {
  metrics: AutomationMetrics | null;
  onRun: () => void;
}) {
  const cards = metrics
    ? [
        { label: "Leads calientes", value: metrics.tasks_pending, icon: Sparkles, tone: "indigo" },
        { label: "Leads fríos", value: metrics.tasks_overdue, icon: Clock, tone: "amber" },
        { label: "Negociaciones detenidas", value: metrics.tasks_total - metrics.tasks_completed, icon: CircleDashed, tone: "slate" },
        { label: "Clientes VIP inactivos", value: metrics.alerts_critical, icon: AlertTriangle, tone: "rose" },
        { label: "Pedidos en riesgo", value: metrics.by_task_type?.order_risk || 0, icon: ListChecks, tone: "slate" },
        { label: "Inventario crítico", value: metrics.by_task_type?.inventory_check || 0, icon: Inbox, tone: "slate" }
      ]
    : [];
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-800">
          Centro de alertas
        </h3>
        <Button size="sm" variant="outline" onClick={onRun}>
          <RefreshCw className="mr-1 h-3 w-3" /> Ejecutar motor
        </Button>
      </div>
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {cards.map((c) => (
          <Card key={c.label} className="border-slate-200">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-xs uppercase tracking-wide text-slate-500">
                {c.label}
              </CardTitle>
              <c.icon className="h-4 w-4 text-slate-400" />
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-semibold text-slate-900">{c.value}</p>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

export function AutomationWorkspace() {
  const { accessToken, refreshSession } = useAuthStore();
  const [view, setView] = useState<View>("board");
  const [board, setBoard] = useState<AutomationTaskBoard | null>(null);
  const [tasks, setTasks] = useState<AutomationTask[]>([]);
  const [calendar, setCalendar] = useState<import("@/types/automation").AutomationCalendarView | null>(null);
  const [calendarView, setCalendarView] = useState<"day" | "week" | "month">("week");
  const [metrics, setMetrics] = useState<AutomationMetrics | null>(null);
  const [loading, setLoading] = useState(false);
  const [running, setRunning] = useState(false);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [priorityFilter, setPriorityFilter] = useState<string>("");
  const [lastRun, setLastRun] = useState<string | null>(null);

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
      const [b, m, ts] = await Promise.all([
        runWithAuth((t) => automationService.fetchTaskBoard(t)),
        runWithAuth((t) => automationService.fetchMetrics(t)),
        runWithAuth((t) =>
          automationService.fetchTasks(t, {
            search: search || undefined,
            status: statusFilter || undefined,
            priority: priorityFilter || undefined
          })
        )
      ]);
      if (b) setBoard(b);
      if (m) setMetrics(m);
      if (ts) setTasks(ts);
    } finally {
      setLoading(false);
    }
  }, [accessToken, runWithAuth, search, statusFilter, priorityFilter]);

  const reloadCalendar = useCallback(async () => {
    if (!accessToken) return;
    const v = await runWithAuth((t) =>
      automationService.fetchCalendar(t, { view: calendarView })
    );
    if (v) setCalendar(v);
  }, [accessToken, runWithAuth, calendarView]);

  useEffect(() => {
    reload();
  }, [reload]);

  useEffect(() => {
    reloadCalendar();
  }, [reloadCalendar]);

  const handleComplete = useCallback(
    async (id: string) => {
      const updated = await runWithAuth((t) =>
        automationService.completeTask(t, id)
      );
      if (updated) {
        reload();
      }
    },
    [runWithAuth, reload]
  );

  const handleCancel = useCallback(
    async (id: string) => {
      const updated = await runWithAuth((t) =>
        automationService.cancelTask(t, id)
      );
      if (updated) {
        reload();
      }
    },
    [runWithAuth, reload]
  );

  const handleRun = useCallback(async () => {
    if (!accessToken) return;
    setRunning(true);
    try {
      const r = await runWithAuth((t) => automationService.runEngine(t));
      setLastRun(new Date().toLocaleTimeString("es-ES"));
      if (r) {
        reload();
      }
    } finally {
      setRunning(false);
    }
  }, [accessToken, runWithAuth, reload]);

  const tabs = useMemo(
    () => [
      { key: "board", label: "Task Center", icon: ListChecks },
      { key: "list", label: "Todas", icon: Inbox },
      { key: "calendar", label: "Calendario", icon: Calendar },
      { key: "alerts", label: "Alertas", icon: AlertTriangle }
    ],
    []
  );

  return (
    <div className="flex flex-col gap-4">
      <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          title="Tareas abiertas"
          value={String(metrics?.tasks_pending ?? 0)}
          icon={ListChecks}
          trend={metrics ? `${metrics.tasks_today} hoy` : "—"}
        />
        <MetricCard
          title="Vencidas"
          value={String(metrics?.tasks_overdue ?? 0)}
          icon={AlertTriangle}
          trend={metrics ? `${metrics.tasks_this_week} esta semana` : "—"}
        />
        <MetricCard
          title="Tasa de cierre"
          value={`${metrics?.tasks_completion_rate_pct ?? 0}%`}
          icon={CheckCircle2}
          trend={metrics ? `${metrics.tasks_completed} hechas` : "—"}
        />
        <MetricCard
          title="Reglas activas"
          value={`${metrics?.rules_enabled ?? 0}/${metrics?.rules_total ?? 0}`}
          icon={Play}
          trend={
            metrics
              ? `${metrics.automation_executions} ejecuciones`
              : "—"
          }
        />
      </div>

      <Card>
        <CardContent className="flex flex-wrap items-center justify-between gap-2 p-3">
          <div className="flex items-center gap-1 rounded-lg border border-slate-200 bg-white p-0.5">
            {tabs.map((t) => (
              <button
                key={t.key}
                type="button"
                onClick={() => setView(t.key as View)}
                className={`flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium ${
                  view === t.key
                    ? "bg-indigo-600 text-white"
                    : "text-slate-600 hover:bg-slate-50"
                }`}
              >
                <t.icon className="h-3.5 w-3.5" /> {t.label}
              </button>
            ))}
          </div>
          <div className="flex items-center gap-2">
            <div className="relative">
              <Search className="pointer-events-none absolute left-2 top-2.5 h-3.5 w-3.5 text-slate-400" />
              <input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Buscar tarea"
                className="h-8 rounded-md border border-slate-200 bg-white pl-7 pr-2 text-xs"
              />
            </div>
            <div className="flex items-center gap-1">
              <Filter className="h-3.5 w-3.5 text-slate-400" />
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="h-8 rounded-md border border-slate-200 bg-white px-2 text-xs"
              >
                <option value="">Estado</option>
                <option value="pending">Pendiente</option>
                <option value="in_progress">En curso</option>
                <option value="overdue">Vencida</option>
                <option value="completed">Completada</option>
              </select>
              <select
                value={priorityFilter}
                onChange={(e) => setPriorityFilter(e.target.value)}
                className="h-8 rounded-md border border-slate-200 bg-white px-2 text-xs"
              >
                <option value="">Prioridad</option>
                <option value="critical">Crítica</option>
                <option value="high">Alta</option>
                <option value="medium">Media</option>
                <option value="low">Baja</option>
              </select>
            </div>
            <Button size="sm" onClick={handleRun} disabled={running}>
              {running ? (
                <Loader2 className="mr-1 h-3 w-3 animate-spin" />
              ) : (
                <RefreshCw className="mr-1 h-3 w-3" />
              )}
              Ejecutar motor
            </Button>
            {lastRun ? (
              <span className="text-[10px] text-slate-500">
                Última: {lastRun}
              </span>
            ) : null}
          </div>
        </CardContent>
      </Card>

      <div>
        {view === "board" ? (
          board ? (
            <BoardView
              board={board}
              onComplete={handleComplete}
              onCancel={handleCancel}
            />
          ) : (
            <p className="text-xs text-slate-500">Cargando…</p>
          )
        ) : null}
        {view === "list" ? (
          <ListView
            tasks={tasks}
            onComplete={handleComplete}
            onCancel={handleCancel}
          />
        ) : null}
        {view === "calendar" ? (
          <CalendarView
            entries={calendar?.entries ?? []}
            view={calendarView}
            onChangeView={setCalendarView}
          />
        ) : null}
        {view === "alerts" ? (
          <AlertsView metrics={metrics} onRun={handleRun} />
        ) : null}
      </div>
    </div>
  );
}
