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
  X,
  type LucideIcon
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { MetricCard } from "@/components/ui/metric-card";
import { Skeleton } from "@/components/ui/skeleton";
import { StatusPill } from "@/components/ui/status-pill";
import { EmptyState } from "@/components/feedback/empty-state";
import { Kbd } from "@/components/ui/kbd";
import { cn } from "@/lib/utils";
import { useAuthStore } from "@/store/auth-store";
import * as automationService from "@/services/automation.service";
import type {
  AutomationCalendarEntry,
  AutomationMetrics,
  AutomationTask,
  AutomationTaskBoard
} from "@/types/automation";

type View = "board" | "list" | "calendar" | "alerts";

const PRIORITY_TONE: Record<string, "destructive" | "warning" | "primary" | "info" | "neutral"> = {
  critical: "destructive",
  high: "warning",
  medium: "primary",
  low: "neutral"
};

const STATUS_TONE: Record<string, "success" | "warning" | "primary" | "info" | "destructive" | "neutral"> = {
  completed: "success",
  pending: "info",
  in_progress: "primary",
  overdue: "destructive",
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

function isOverdue(task: AutomationTask): boolean {
  if (task.status === "completed" || task.status === "cancelled") return false;
  if (task.status === "overdue") return true;
  if (!task.due_date) return false;
  return new Date(task.due_date).getTime() < Date.now();
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
  const overdue = isOverdue(task);
  return (
    <Card
      className={cn(
        "group transition-all hover:-translate-y-px hover:shadow-md",
        overdue && "ring-1 ring-destructive/30"
      )}
    >
      <CardContent className="space-y-2.5 p-4">
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-semibold tracking-tight text-foreground">
              {task.title}
            </p>
            <p className="mt-0.5 text-xs text-muted-foreground">
              {TYPE_LABEL[task.task_type] || task.task_type}
              {task.due_date ? ` · Vence ${formatDate(task.due_date)}` : ""}
            </p>
          </div>
          <StatusPill tone={PRIORITY_TONE[task.priority] || "neutral"} size="sm">
            {PRIORITY_LABEL[task.priority] || task.priority}
          </StatusPill>
        </div>
        {task.description ? (
          <p className="line-clamp-2 text-xs text-muted-foreground">
            {task.description}
          </p>
        ) : null}
        {task.ai_next_action ? (
          <div className="flex items-center gap-1.5 rounded-md border border-primary-100 bg-primary-50/60 px-2 py-1.5 text-xs text-primary-700 dark:bg-primary-50/20 dark:border-primary-200/30 dark:text-primary-200">
            <Sparkles className="h-3.5 w-3.5" aria-hidden="true" />
            <span className="line-clamp-1">{task.ai_next_action}</span>
            {typeof task.ai_score === "number" ? (
              <span className="ml-auto rounded bg-card px-1.5 text-[10px] font-semibold uppercase tracking-wider text-primary">
                Score {task.ai_score}
              </span>
            ) : null}
          </div>
        ) : null}
        <div className="flex items-center gap-2 pt-1">
          <StatusPill tone={STATUS_TONE[task.status] || "neutral"} size="sm">
            {STATUS_LABEL[task.status] || task.status}
          </StatusPill>
          {task.status !== "completed" && task.status !== "cancelled" ? (
            <>
              <Button
                size="sm"
                variant="success"
                onClick={() => onComplete(task.id)}
                className="ml-auto h-7 text-xs"
              >
                <CheckCircle2 className="mr-1 h-3 w-3" aria-hidden="true" />
                Completar
              </Button>
              <Button
                size="sm"
                variant="ghost"
                onClick={() => onCancel(task.id)}
                className="h-7 text-xs"
                aria-label="Cancelar tarea"
              >
                <X className="h-3 w-3" aria-hidden="true" />
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
          <div className="flex items-center justify-between rounded-lg border border-border bg-muted/40 px-3 py-2">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-foreground">
              {col.label}
            </h3>
            <StatusPill tone="neutral" size="sm">
              {col.count}
            </StatusPill>
          </div>
          <div className="flex max-h-[60vh] flex-col gap-2 overflow-y-auto pr-1">
            {col.tasks.length === 0 ? (
              <div className="rounded-md border border-dashed border-border bg-muted/30 px-3 py-6 text-center text-xs text-muted-foreground">
                Sin tareas
              </div>
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
  if (tasks.length === 0) {
    return (
      <EmptyState
        icon={Inbox}
        title="No hay tareas"
        description="Ajusta los filtros o ejecuta el motor de automatización para generar nuevas tareas."
      />
    );
  }
  return (
    <Card>
      <div className="overflow-x-auto">
        <table className="min-w-full text-sm">
          <thead className="border-b border-border bg-muted/40 text-left text-xs uppercase tracking-wider text-muted-foreground">
            <tr>
              <th className="px-3 py-2 font-medium">Tarea</th>
              <th className="px-3 py-2 font-medium">Tipo</th>
              <th className="px-3 py-2 font-medium">Prioridad</th>
              <th className="px-3 py-2 font-medium">Estado</th>
              <th className="px-3 py-2 font-medium">Vence</th>
              <th className="px-3 py-2 font-medium">IA</th>
              <th className="px-3 py-2 text-right font-medium">Acciones</th>
            </tr>
          </thead>
          <tbody>
            {tasks.map((t) => (
              <tr
                key={t.id}
                className="border-b border-border/60 transition hover:bg-muted/30"
              >
                <td className="max-w-[260px] truncate px-3 py-2 font-medium text-foreground">
                  {t.title}
                </td>
                <td className="px-3 py-2 text-xs text-muted-foreground">
                  {TYPE_LABEL[t.task_type] || t.task_type}
                </td>
                <td className="px-3 py-2">
                  <StatusPill tone={PRIORITY_TONE[t.priority] || "neutral"} size="sm">
                    {PRIORITY_LABEL[t.priority] || t.priority}
                  </StatusPill>
                </td>
                <td className="px-3 py-2">
                  <StatusPill tone={STATUS_TONE[t.status] || "neutral"} size="sm">
                    {STATUS_LABEL[t.status] || t.status}
                  </StatusPill>
                </td>
                <td className="px-3 py-2 text-xs text-muted-foreground">
                  {formatDate(t.due_date)}
                </td>
                <td className="px-3 py-2 text-xs text-muted-foreground">
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
                        onClick={() => onComplete(t.id)}
                      >
                        <CheckCircle2 className="mr-1 h-3 w-3" />
                        Hecho
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => onCancel(t.id)}
                      >
                        Cancelar
                      </Button>
                    </div>
                  ) : null}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
}

function CalendarView({
  entries,
  view,
  onChangeView
}: {
  entries: AutomationCalendarEntry[];
  view: "day" | "week" | "month";
  onChangeView: (v: "day" | "week" | "month") => void;
}) {
  return (
    <div className="space-y-3">
      <div className="inline-flex items-center gap-1 rounded-lg border border-input bg-card p-0.5">
        {(["day", "week", "month"] as const).map((v) => (
          <button
            type="button"
            key={v}
            onClick={() => onChangeView(v)}
            className={cn(
              "rounded-md px-3 py-1.5 text-xs font-medium transition",
              v === view
                ? "bg-primary text-primary-foreground shadow-xs"
                : "text-muted-foreground hover:bg-muted hover:text-foreground"
            )}
          >
            {v === "day" ? "Día" : v === "week" ? "Semana" : "Mes"}
          </button>
        ))}
      </div>
      <Card>
        <div className="divide-y divide-border">
          {entries.length === 0 ? (
            <div className="px-4 py-8 text-center text-xs text-muted-foreground">
              Sin seguimientos programados
            </div>
          ) : (
            entries.map((e) => (
              <div
                key={e.task_id}
                className="flex items-center gap-3 px-4 py-2.5 text-sm transition hover:bg-muted/30"
              >
                <span className="flex h-7 w-7 items-center justify-center rounded-md bg-primary-50 text-primary">
                  <Calendar className="h-3.5 w-3.5" aria-hidden="true" />
                </span>
                <span className="font-medium text-foreground">{e.title}</span>
                <span className="text-xs text-muted-foreground">
                  {formatDate(e.due_date)}
                </span>
                <StatusPill tone={PRIORITY_TONE[e.priority] || "neutral"} size="sm">
                  {PRIORITY_LABEL[e.priority] || e.priority}
                </StatusPill>
                <span className="ml-auto text-[10px] uppercase tracking-wider text-muted-foreground">
                  {TYPE_LABEL[e.task_type] || e.task_type}
                </span>
              </div>
            ))
          )}
        </div>
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
  const cards: Array<{
    label: string;
    value: number;
    icon: LucideIcon;
    tone: "destructive" | "warning" | "info" | "primary" | "purple" | "success";
  }> = metrics
    ? [
        { label: "Leads calientes", value: metrics.tasks_pending, icon: Sparkles, tone: "primary" },
        { label: "Leads fríos", value: metrics.tasks_overdue, icon: Clock, tone: "warning" },
        { label: "Negociaciones detenidas", value: metrics.tasks_total - metrics.tasks_completed, icon: CircleDashed, tone: "info" },
        { label: "Clientes VIP inactivos", value: metrics.alerts_critical, icon: AlertTriangle, tone: "destructive" },
        { label: "Pedidos en riesgo", value: metrics.by_task_type?.order_risk || 0, icon: ListChecks, tone: "warning" },
        { label: "Inventario crítico", value: metrics.by_task_type?.inventory_check || 0, icon: Inbox, tone: "purple" }
      ]
    : [];
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold tracking-tight text-foreground">
            Centro de alertas
          </h3>
          <p className="mt-0.5 text-xs text-muted-foreground">
            Métricas en tiempo real del motor de automatización
          </p>
        </div>
        <Button variant="outline" onClick={onRun}>
          <RefreshCw className="mr-1.5 h-3.5 w-3.5" aria-hidden="true" />
          Ejecutar motor
        </Button>
      </div>
      {cards.length === 0 ? (
        <Skeleton className="h-40 w-full rounded-xl" />
      ) : (
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {cards.map((c) => (
            <MetricCard
              key={c.label}
              title={c.label}
              value={String(c.value)}
              icon={c.icon}
              iconTone={c.tone}
            />
          ))}
        </div>
      )}
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
          iconTone="primary"
          trend={metrics ? `${metrics.tasks_today} hoy` : "—"}
        />
        <MetricCard
          title="Vencidas"
          value={String(metrics?.tasks_overdue ?? 0)}
          icon={AlertTriangle}
          iconTone="destructive"
          trend={metrics ? `${metrics.tasks_this_week} esta semana` : "—"}
        />
        <MetricCard
          title="Tasa de cierre"
          value={`${metrics?.tasks_completion_rate_pct ?? 0}%`}
          icon={CheckCircle2}
          iconTone="success"
          trend={metrics ? `${metrics.tasks_completed} hechas` : "—"}
        />
        <MetricCard
          title="Reglas activas"
          value={`${metrics?.rules_enabled ?? 0}/${metrics?.rules_total ?? 0}`}
          icon={Play}
          iconTone="purple"
          trend={metrics ? `${metrics.automation_executions} ejecuciones` : "—"}
        />
      </div>

      <Card variant="elevated">
        <CardContent className="flex flex-wrap items-center justify-between gap-3 p-3">
          <div className="inline-flex items-center gap-1 rounded-lg border border-input bg-card p-0.5">
            {tabs.map((t) => (
              <button
                key={t.key}
                type="button"
                onClick={() => setView(t.key as View)}
                className={cn(
                  "flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium transition",
                  view === t.key
                    ? "bg-primary text-primary-foreground shadow-xs"
                    : "text-muted-foreground hover:bg-muted hover:text-foreground"
                )}
              >
                <t.icon className="h-3.5 w-3.5" />
                {t.label}
              </button>
            ))}
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <div className="relative">
              <Search className="pointer-events-none absolute left-2 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
              <input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Buscar tarea"
                className="h-8 w-44 rounded-md border border-input bg-background pl-7 pr-2 text-xs shadow-xs focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              />
            </div>
            <div className="inline-flex items-center gap-1">
              <Filter className="h-3.5 w-3.5 text-muted-foreground" />
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="h-8 rounded-md border border-input bg-background px-2 text-xs shadow-xs focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
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
                className="h-8 rounded-md border border-input bg-background px-2 text-xs shadow-xs focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
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
                <Loader2 className="mr-1.5 h-3.5 w-3.5 animate-spin" />
              ) : (
                <RefreshCw className="mr-1.5 h-3.5 w-3.5" />
              )}
              Ejecutar motor
            </Button>
            {lastRun ? (
              <Kbd>
                <Clock className="mr-1 inline h-3 w-3" aria-hidden="true" />
                {lastRun}
              </Kbd>
            ) : null}
          </div>
        </CardContent>
      </Card>

      <div>
        {view === "board" ? (
          loading && !board ? (
            <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-5">
              {Array.from({ length: 5 }).map((_, i) => (
                <Skeleton key={i} className="h-40 w-full rounded-xl" />
              ))}
            </div>
          ) : board ? (
            <BoardView
              board={board}
              onComplete={handleComplete}
              onCancel={handleCancel}
            />
          ) : null
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
