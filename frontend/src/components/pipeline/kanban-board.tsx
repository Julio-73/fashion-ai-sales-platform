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

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { usePipelineStore } from "@/store/pipeline-store";
import type { PipelineItem } from "@/types/pipeline";

import { KanbanColumn } from "./kanban-column";

const SEVERITY_TONE: Record<string, string> = {
  critical: "bg-rose-100 text-rose-700 ring-rose-200",
  warning: "bg-amber-100 text-amber-700 ring-amber-200",
  info: "bg-sky-100 text-sky-700 ring-sky-200"
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
  NEAR_BUDGET_OVERFLOW: "Concentración de valor"
};

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

  function handleDragStart(e: React.DragEvent<HTMLDivElement>, deal: PipelineItem) {
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

  return (
    <div className="flex h-full flex-col gap-4">
      <div className="flex flex-wrap items-center gap-2">
        <div className="relative flex-1 min-w-[180px]">
          <Search className="absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-slate-400" />
          <input
            value={store.filters.search}
            onChange={(e) => store.setSearch(e.target.value)}
            placeholder="Buscar deal…"
            className="w-full rounded-lg border border-slate-200 bg-white py-1.5 pl-8 pr-2 text-sm focus:border-indigo-400 focus:outline-none"
          />
        </div>
        <div className="flex items-center gap-1 rounded-lg border border-slate-200 bg-white p-0.5">
          <Filter className="h-3.5 w-3.5 text-slate-400" />
          {[
            { key: "open", label: "Abiertos", v: true },
            { key: "closed", label: "Cerrados", v: false },
            { key: "all", label: "Todos", v: null }
          ].map((opt) => (
            <button
              key={opt.key}
              type="button"
              onClick={() => store.setOpenFilter(opt.v as boolean | null)}
              className={`rounded-md px-2.5 py-1 text-xs font-medium ${
                store.filters.is_open === opt.v
                  ? "bg-indigo-600 text-white"
                  : "text-slate-600 hover:bg-slate-50"
              }`}
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
          <RefreshCcw className="mr-1.5 h-3.5 w-3.5" />
          Actualizar
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={() => setShowRecs((v) => !v)}
        >
          <Sparkles className="mr-1.5 h-3.5 w-3.5 text-amber-500" />
          IA
          {showRecs ? <ChevronUp className="ml-1 h-3 w-3" /> : <ChevronDown className="ml-1 h-3 w-3" />}
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={() => setShowAlerts((v) => !v)}
        >
          <Bell className="mr-1.5 h-3.5 w-3.5" />
          Alertas
          {(store.alerts?.total ?? 0) > 0 ? (
            <span className="ml-1 rounded-full bg-rose-500 px-1.5 text-[10px] font-bold text-white">
              {store.alerts?.total}
            </span>
          ) : null}
          {showAlerts ? <ChevronUp className="ml-1 h-3 w-3" /> : <ChevronDown className="ml-1 h-3 w-3" />}
        </Button>
      </div>

      {showAlerts && (store.alerts?.alerts.length ?? 0) > 0 ? (
        <Card className="border-amber-200 bg-amber-50/60">
          <CardContent className="p-3">
            <div className="mb-2 flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-amber-600" />
              <h4 className="text-sm font-semibold text-amber-800">
                Automatizaciones activas
              </h4>
              <span className="text-xs text-amber-700">
                ({store.alerts?.total})
              </span>
            </div>
            <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
              {store.alerts?.alerts.slice(0, 6).map((a) => (
                <div
                  key={a.id}
                  className="rounded-lg border border-amber-200 bg-white p-2 text-xs"
                >
                  <div className="flex items-center gap-1.5">
                    <span
                      className={`rounded-full px-1.5 py-0.5 text-[10px] font-semibold ring-1 ${
                        SEVERITY_TONE[a.severity]
                      }`}
                    >
                      {SEVERITY_LABEL[a.severity]}
                    </span>
                    <span className="font-medium text-slate-700">
                      {RULE_LABEL[a.rule] ?? a.rule}
                    </span>
                  </div>
                  <div className="mt-1 font-semibold text-slate-800 line-clamp-1">
                    {a.deal_title}
                  </div>
                  <div className="mt-0.5 text-slate-600 line-clamp-2">
                    {a.message}
                  </div>
                  <div className="mt-1 text-[10px] text-indigo-600">
                    {a.suggested_action}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      ) : null}

      {showRecs && (store.recommendations?.recommendations.length ?? 0) > 0 ? (
        <Card className="border-indigo-200 bg-indigo-50/40">
          <CardContent className="p-3">
            <div className="mb-2 flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-indigo-500" />
              <h4 className="text-sm font-semibold text-indigo-800">
                Recomendaciones IA (top {Math.min(5, store.recommendations?.total ?? 0)})
              </h4>
            </div>
            <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
              {store.recommendations?.recommendations.slice(0, 6).map((r) => {
                const deal = store.board?.items.find((d) => d.id === r.deal_id);
                return (
                  <div
                    key={r.deal_id}
                    className="rounded-lg border border-indigo-200 bg-white p-2 text-xs"
                  >
                    <div className="flex items-center gap-2">
                      <span
                        className={`rounded-full px-2 py-0.5 text-[10px] font-bold ${
                          r.score >= 75
                            ? "bg-emerald-50 text-emerald-700"
                            : r.score >= 45
                            ? "bg-amber-50 text-amber-700"
                            : "bg-slate-100 text-slate-700"
                        }`}
                      >
                        {r.score}
                      </span>
                      <span className="line-clamp-1 font-medium text-slate-800">
                        {deal?.title ?? r.deal_id}
                      </span>
                    </div>
                    <div className="mt-1 text-slate-600 line-clamp-2">
                      {r.next_best_action}
                    </div>
                    {r.suggested_channel ? (
                      <div className="mt-0.5 text-[10px] text-slate-500">
                        Canal sugerido: <strong>{r.suggested_channel}</strong>
                      </div>
                    ) : null}
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      ) : null}

      {store.metrics ? (
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
          {[
            {
              label: "Abiertos",
              value: store.metrics.total_open,
              tone: "bg-indigo-50 text-indigo-700"
            },
            {
              label: "Valor abierto",
              value: store.metrics.open_value.toLocaleString("es-ES", {
                style: "currency",
                currency: "USD",
                maximumFractionDigits: 0
              }),
              tone: "bg-emerald-50 text-emerald-700"
            },
            {
              label: "Ponderado",
              value: store.metrics.weighted_open_value.toLocaleString("es-ES", {
                style: "currency",
                currency: "USD",
                maximumFractionDigits: 0
              }),
              tone: "bg-violet-50 text-violet-700"
            },
            {
              label: "Conversión",
              value: `${store.metrics.conversion_rate_pct}%`,
              tone: "bg-amber-50 text-amber-700"
            }
          ].map((m) => (
            <div
              key={m.label}
              className={`rounded-lg p-2 ${m.tone}`}
            >
              <div className="text-[10px] uppercase tracking-wide opacity-70">
                {m.label}
              </div>
              <div className="mt-0.5 text-lg font-bold">{m.value}</div>
            </div>
          ))}
        </div>
      ) : null}

      {store.error ? (
        <div className="rounded-lg border border-rose-200 bg-rose-50 p-2 text-xs text-rose-700">
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
                  className="h-96 w-72"
                />
              ))}
            </div>
          ) : null}
          {!store.isLoading && store.stages.length === 0 ? (
            <div className="flex flex-1 items-center justify-center text-sm text-slate-500">
              <BarChart3 className="mr-2 h-4 w-4" />
              No hay etapas configuradas
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
