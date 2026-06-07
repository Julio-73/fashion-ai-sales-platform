"use client";

import { useMemo, useState } from "react";
import {
  AlertTriangle,
  BarChart3,
  Bell,
  ChevronDown,
  ChevronUp,
  Filter,
  RefreshCcw,
  Search,
  Sparkles
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { StatusPill } from "@/components/ui/status-pill";
import { Kbd } from "@/components/ui/kbd";
import { cn } from "@/lib/utils";
import { usePipelineStore } from "@/store/pipeline-store";
import { formatCurrency } from "@/modules/crm/utils/format";
import type { PipelineItem } from "@/types/pipeline";

import { KanbanColumn } from "./kanban-column";

const SEVERITY_TONE: Record<string, "destructive" | "warning" | "info"> = {
  critical: "destructive",
  warning: "warning",
  info: "info"
};

const SEVERITY_LABEL: Record<string, string> = {
  critical: "Crítico",
  warning: "Atención",
  info: "Info"
};

const RULE_LABEL: Record<string, string> = {
  STUCK_IN_STAGE: "Estancado",
  COLD_LEAD: "Lead frío",
  VIP_IGNORED: "VIP olvidado",
  HIGH_INTENT_SILENT: "Score alto sin mover",
  NEAR_BUDGET_OVERFLOW: "Concentración de valor",
  NO_ACTIVITY_48H: "Sin actividad 48 h",
  NEGOTIATION_STUCK_7D: "Estancado en negociación",
  WON_DEAL: "Deal ganado",
  LOST_DEAL: "Deal perdido"
};

type FilterOpt = "open" | "closed" | "all";

export function KanbanBoard() {
  const store = usePipelineStore();
  const [draggingDeal, setDraggingDeal] = useState<PipelineItem | null>(null);
  const [dragOverStage, setDragOverStage] = useState<string | null>(null);
  const [showAlerts, setShowAlerts] = useState(true);
  const [showRecs, setShowRecs] = useState(false);

  const grouped = useMemo(() => {
    const out: Record<string, PipelineItem[]> = {};
    store.stages.forEach((s) => {
      out[s.key] = [];
    });
    (store.board?.items ?? []).forEach((d) => {
      if (out[d.stage]) {
        out[d.stage].push(d);
      } else {
        out[d.stage] = [d];
      }
    });
    return out;
  }, [store.board, store.stages]);

  function handleDragStart(
    e: React.DragEvent<HTMLDivElement>,
    deal: PipelineItem
  ) {
    e.dataTransfer.setData("text/plain", deal.id);
    e.dataTransfer.effectAllowed = "move";
    setDraggingDeal(deal);
  }

  function handleDragEnd() {
    setDraggingDeal(null);
    setDragOverStage(null);
  }

  function handleDragOverColumn(stageKey: string) {
    setDragOverStage(stageKey);
  }

  async function handleDropOnColumn(stageKey: string) {
    const deal = draggingDeal;
    setDragOverStage(null);
    setDraggingDeal(null);
    if (!deal || deal.stage === stageKey) return;
    const target = store.stages.find((s) => s.key === stageKey);
    if (!target) return;
    if (target.is_terminal) return;
    const probability = target.default_probability;
    await store.moveStage(deal.id, stageKey, { probability });
  }

  const openFilterValue =
    store.filters.is_open === true
      ? "open"
      : store.filters.is_open === false
        ? "closed"
        : "all";

  return (
    <div className="flex h-full flex-col gap-4">
      <div className="flex flex-wrap items-center gap-2">
        <div className="relative min-w-[180px] flex-1">
          <Search className="pointer-events-none absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
          <input
            value={store.filters.search}
            onChange={(e) => store.setSearch(e.target.value)}
            placeholder="Buscar deal…"
            className="w-full rounded-lg border border-input bg-background py-1.5 pl-8 pr-12 text-sm shadow-xs placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          />
          <Kbd className="pointer-events-none absolute right-2 top-1/2 -translate-y-1/2">
            /
          </Kbd>
        </div>
        <div className="inline-flex items-center gap-1 rounded-lg border border-input bg-background p-0.5">
          <Filter className="ml-1 h-3.5 w-3.5 text-muted-foreground" />
          {(
            [
              { key: "open", label: "Abiertos" },
              { key: "closed", label: "Cerrados" },
              { key: "all", label: "Todos" }
            ] satisfies { key: FilterOpt; label: string }[]
          ).map((opt) => (
            <button
              key={opt.key}
              type="button"
              onClick={() =>
                store.setOpenFilter(
                  opt.key === "open"
                    ? true
                    : opt.key === "closed"
                      ? false
                      : null
                )
              }
              className={cn(
                "rounded-md px-2.5 py-1 text-xs font-medium transition",
                openFilterValue === opt.key
                  ? "bg-primary text-primary-foreground shadow-xs"
                  : "text-muted-foreground hover:bg-muted hover:text-foreground"
              )}
            >
              {opt.label}
            </button>
          ))}
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => store.refreshAll()}
          disabled={store.isLoading}
        >
          <RefreshCcw
            className={cn(
              "mr-1.5 h-3.5 w-3.5",
              store.isLoading && "animate-spin"
            )}
          />
          Actualizar
        </Button>
        <Button
          variant={showRecs ? "gradient" : "outline"}
          size="sm"
          onClick={() => setShowRecs((v) => !v)}
        >
          <Sparkles
            className={cn(
              "mr-1.5 h-3.5 w-3.5",
              showRecs ? "" : "text-warning"
            )}
          />
          IA
          {showRecs ? (
            <ChevronUp className="ml-1 h-3 w-3" />
          ) : (
            <ChevronDown className="ml-1 h-3 w-3" />
          )}
        </Button>
        <Button
          variant={showAlerts ? "destructive" : "outline"}
          size="sm"
          onClick={() => setShowAlerts((v) => !v)}
        >
          <Bell className="mr-1.5 h-3.5 w-3.5" />
          Alertas
          {(store.alerts?.total ?? 0) > 0 ? (
            <span
              className={cn(
                "ml-1 rounded-full px-1.5 text-[10px] font-bold",
                showAlerts
                  ? "bg-white/20 text-white"
                  : "bg-destructive text-destructive-foreground"
              )}
            >
              {store.alerts?.total}
            </span>
          ) : null}
          {showAlerts ? (
            <ChevronUp className="ml-1 h-3 w-3" />
          ) : (
            <ChevronDown className="ml-1 h-3 w-3" />
          )}
        </Button>
      </div>

      <AnimatePresence initial={false}>
        {showAlerts && (store.alerts?.alerts.length ?? 0) > 0 ? (
          <motion.div
            key="alerts"
            initial={{ opacity: 0, y: -8, height: 0 }}
            animate={{ opacity: 1, y: 0, height: "auto" }}
            exit={{ opacity: 0, y: -8, height: 0 }}
            transition={{ duration: 0.18 }}
          >
            <Card variant="glass" className="border-warning-200/60">
              <CardContent className="p-3">
                <div className="mb-2 flex items-center gap-2">
                  <span className="flex h-6 w-6 items-center justify-center rounded-md bg-warning-50 text-warning-700">
                    <AlertTriangle className="h-3.5 w-3.5" />
                  </span>
                  <h4 className="text-sm font-semibold tracking-tight text-foreground">
                    Automatizaciones activas
                  </h4>
                  <StatusPill tone="warning" size="sm">
                    {store.alerts?.total}
                  </StatusPill>
                </div>
                <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
                  {store.alerts?.alerts.slice(0, 6).map((a) => (
                    <div
                      key={a.id}
                      className="rounded-lg border border-border bg-card p-2 text-xs shadow-xs transition hover:shadow-sm"
                    >
                      <div className="flex items-center gap-1.5">
                        <StatusPill tone={SEVERITY_TONE[a.severity]} size="sm">
                          {SEVERITY_LABEL[a.severity]}
                        </StatusPill>
                        <span className="font-medium text-foreground">
                          {RULE_LABEL[a.rule] ?? a.rule}
                        </span>
                      </div>
                      <div className="mt-1 line-clamp-1 font-semibold text-foreground">
                        {a.deal_title}
                      </div>
                      <div className="mt-0.5 line-clamp-2 text-muted-foreground">
                        {a.message}
                      </div>
                      <div className="mt-1 text-[10px] font-medium text-primary">
                        {a.suggested_action}
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </motion.div>
        ) : null}

        {showRecs &&
        (store.recommendations?.recommendations.length ?? 0) > 0 ? (
          <motion.div
            key="recs"
            initial={{ opacity: 0, y: -8, height: 0 }}
            animate={{ opacity: 1, y: 0, height: "auto" }}
            exit={{ opacity: 0, y: -8, height: 0 }}
            transition={{ duration: 0.18 }}
          >
            <Card variant="glass" className="border-primary-200/60">
              <CardContent className="p-3">
                <div className="mb-2 flex items-center gap-2">
                  <span className="flex h-6 w-6 items-center justify-center rounded-md bg-primary-50 text-primary">
                    <Sparkles className="h-3.5 w-3.5" />
                  </span>
                  <h4 className="text-sm font-semibold tracking-tight text-foreground">
                    Recomendaciones IA
                  </h4>
                  <span className="text-xs text-muted-foreground">
                    (top {Math.min(5, store.recommendations?.total ?? 0)})
                  </span>
                </div>
                <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
                  {store.recommendations?.recommendations
                    .slice(0, 6)
                    .map((r) => {
                      const deal = store.board?.items.find(
                        (d) => d.id === r.deal_id
                      );
                      return (
                        <div
                          key={r.deal_id}
                          className="rounded-lg border border-border bg-card p-2 text-xs shadow-xs transition hover:shadow-sm"
                        >
                          <div className="flex items-center gap-2">
                            <StatusPill
                              tone={
                                r.score >= 75
                                  ? "success"
                                  : r.score >= 45
                                    ? "warning"
                                    : "neutral"
                              }
                              size="sm"
                              icon={<Sparkles className="h-3 w-3" />}
                            >
                              {r.score}
                            </StatusPill>
                            <span className="line-clamp-1 font-medium text-foreground">
                              {deal?.title ?? r.deal_id}
                            </span>
                          </div>
                          <div className="mt-1 line-clamp-2 text-muted-foreground">
                            {r.next_best_action}
                          </div>
                          {r.suggested_channel ? (
                            <div className="mt-0.5 text-[10px] text-muted-foreground">
                              Canal sugerido:{" "}
                              <strong className="text-foreground">
                                {r.suggested_channel}
                              </strong>
                            </div>
                          ) : null}
                        </div>
                      );
                    })}
                </div>
              </CardContent>
            </Card>
          </motion.div>
        ) : null}
      </AnimatePresence>

      {store.metrics ? (
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
          {[
            {
              label: "Abiertos",
              value: store.metrics.total_open.toString(),
              tone: "text-primary",
              bg: "bg-primary-50"
            },
            {
              label: "Valor abierto",
              value: formatCurrency(store.metrics.open_value),
              tone: "text-success",
              bg: "bg-success-50"
            },
            {
              label: "Ponderado",
              value: formatCurrency(store.metrics.weighted_open_value),
              tone: "text-purple",
              bg: "bg-purple-50"
            },
            {
              label: "Conversión",
              value: `${store.metrics.conversion_rate_pct}%`,
              tone: "text-warning",
              bg: "bg-warning-50"
            }
          ].map((m) => (
            <div
              key={m.label}
              className="rounded-lg border border-border bg-card p-2.5 shadow-xs"
            >
              <div className="flex items-center gap-1.5 text-[10px] uppercase tracking-wider text-muted-foreground">
                <span className={cn("h-1.5 w-1.5 rounded-full", m.bg)} />
                {m.label}
              </div>
              <div className={cn("mt-0.5 text-lg font-bold", m.tone)}>
                {m.value}
              </div>
            </div>
          ))}
        </div>
      ) : null}

      {store.error ? (
        <div className="rounded-lg border border-destructive-200 bg-destructive-50 p-2 text-xs text-destructive">
          {store.error}
        </div>
      ) : null}

      <div className="flex-1 overflow-x-auto pb-4">
        <div className="flex h-full gap-3">
          {store.isLoading && !store.board ? (
            <div className="flex gap-3">
              {Array.from({ length: 4 }).map((_, i) => (
                <Skeleton
                  key={i}
                  className="h-96 w-72 rounded-2xl"
                />
              ))}
            </div>
          ) : null}
          {!store.isLoading && store.stages.length === 0 ? (
            <div className="flex flex-1 items-center justify-center rounded-xl border border-dashed border-border bg-muted/30 p-12 text-sm text-muted-foreground">
              <div className="flex flex-col items-center gap-2 text-center">
                <span className="flex h-10 w-10 items-center justify-center rounded-full bg-muted text-muted-foreground">
                  <BarChart3 className="h-5 w-5" />
                </span>
                <p className="font-medium">No hay etapas configuradas</p>
                <p className="text-xs">
                  Crea etapas para empezar a gestionar el pipeline.
                </p>
              </div>
            </div>
          ) : null}
          {store.stages.map((s) => (
            <KanbanColumn
              key={s.key}
              stage={s}
              deals={grouped[s.key] ?? []}
              isLoading={store.isLoading}
              draggingDeal={draggingDeal}
              onDragStart={handleDragStart}
              onDragEnd={handleDragEnd}
              onDragOverColumn={handleDragOverColumn}
              onDropOnColumn={handleDropOnColumn}
              dragOverStage={dragOverStage}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
