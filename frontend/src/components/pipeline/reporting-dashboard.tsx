"use client";

import { Skeleton } from "@/components/ui/skeleton";
import { usePipelineStore } from "@/store/pipeline-store";

function BarRow({
  label,
  value,
  max,
  color
}: {
  label: string;
  value: number;
  max: number;
  color: string;
}) {
  const pct = max > 0 ? Math.max(2, (value / max) * 100) : 0;
  return (
    <div>
      <div className="flex items-center justify-between text-[11px] text-slate-600">
        <span>{label}</span>
        <span className="font-mono font-semibold text-slate-700">
          {value.toLocaleString("es-ES", {
            style: "currency",
            currency: "USD",
            maximumFractionDigits: 0
          })}
        </span>
      </div>
      <div className="mt-1 h-2 w-full overflow-hidden rounded-full bg-slate-100">
        <div
          className="h-full rounded-full"
          style={{ width: `${pct}%`, backgroundColor: color }}
        />
      </div>
    </div>
  );
}

function FunnelView() {
  const { funnel } = usePipelineStore();
  if (!funnel) {
    return (
      <div className="space-y-2">
        {Array.from({ length: 7 }).map((_, i) => (
          <Skeleton key={i} className="h-7 w-full" />
        ))}
      </div>
    );
  }
  const max = Math.max(...funnel.stages.map((s) => s.value), 1);
  return (
    <div className="space-y-2">
      {funnel.stages.map((s) => (
        <div
          key={s.key}
          className="rounded-lg border border-slate-200 bg-white p-2.5"
        >
          <BarRow
            label={`${s.label} · ${s.count} deals`}
            value={s.value}
            max={max}
            color={s.color}
          />
        </div>
      ))}
    </div>
  );
}

function MetricsView() {
  const { metrics } = usePipelineStore();
  if (!metrics) {
    return (
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
        {Array.from({ length: 6 }).map((_, i) => (
          <Skeleton key={i} className="h-20" />
        ))}
      </div>
    );
  }
  const cards = [
    { label: "Total abiertos", value: metrics.total_open, footer: "deals" },
    { label: "Ganados", value: metrics.total_closed_won, footer: "cerrados" },
    { label: "Perdidos", value: metrics.total_closed_lost, footer: "cerrados" },
    {
      label: "Conversión",
      value: `${metrics.conversion_rate_pct}%`,
      footer: "sobre cerrados"
    },
    {
      label: "Tiempo medio cierre",
      value: `${metrics.average_time_to_close_days}d`,
      footer: "promedio"
    },
    {
      label: "Estancado más antiguo",
      value: `${metrics.oldest_unstuck_days}d`,
      footer: "en etapa actual"
    }
  ];
  return (
    <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
      {cards.map((c) => (
        <div
          key={c.label}
          className="rounded-lg border border-slate-200 bg-white p-3"
        >
          <div className="text-[10px] uppercase tracking-wide text-slate-500">
            {c.label}
          </div>
          <div className="mt-1 text-xl font-bold text-slate-800">{c.value}</div>
          <div className="text-[10px] text-slate-400">{c.footer}</div>
        </div>
      ))}
    </div>
  );
}

function BreakdownsView() {
  const { metrics } = usePipelineStore();
  if (!metrics) return null;
  return (
    <div className="grid gap-3 lg:grid-cols-2">
      <div className="rounded-lg border border-slate-200 bg-white p-3">
        <h4 className="mb-2 text-xs font-semibold text-slate-700">
          Por canal
        </h4>
        <div className="space-y-1.5">
          {Object.entries(metrics.by_channel).map(([k, v]) => (
            <div
              key={k}
              className="flex items-center justify-between text-xs"
            >
              <span className="capitalize text-slate-600">{k}</span>
              <span className="font-mono font-semibold text-slate-800">
                {v.count} ·{" "}
                {v.value.toLocaleString("es-ES", {
                  style: "currency",
                  currency: "USD",
                  maximumFractionDigits: 0
                })}
              </span>
            </div>
          ))}
          {Object.keys(metrics.by_channel).length === 0 ? (
            <div className="text-xs text-slate-400">Sin datos</div>
          ) : null}
        </div>
      </div>
      <div className="rounded-lg border border-slate-200 bg-white p-3">
        <h4 className="mb-2 text-xs font-semibold text-slate-700">
          Por prioridad
        </h4>
        <div className="space-y-1.5">
          {Object.entries(metrics.by_priority).map(([k, v]) => (
            <div
              key={k}
              className="flex items-center justify-between text-xs"
            >
              <span className="capitalize text-slate-600">{k}</span>
              <span className="font-mono font-semibold text-slate-800">
                {v.count} deals
              </span>
            </div>
          ))}
          {Object.keys(metrics.by_priority).length === 0 ? (
            <div className="text-xs text-slate-400">Sin datos</div>
          ) : null}
        </div>
      </div>
    </div>
  );
}

function TopDealsView() {
  const { dashboard } = usePipelineStore();
  if (!dashboard) {
    return (
      <div className="space-y-2">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-12 w-full" />
        ))}
      </div>
    );
  }
  if (dashboard.top_deals.length === 0) {
    return (
      <div className="rounded-lg border border-dashed border-slate-300 bg-white p-4 text-center text-sm text-slate-500">
        Aún no hay deals abiertos para rankear.
      </div>
    );
  }
  return (
    <div className="overflow-hidden rounded-lg border border-slate-200 bg-white">
      <table className="w-full text-sm">
        <thead className="bg-slate-50 text-[10px] uppercase tracking-wide text-slate-500">
          <tr>
            <th className="px-3 py-2 text-left">Deal</th>
            <th className="px-3 py-2 text-left">Etapa</th>
            <th className="px-3 py-2 text-right">Valor</th>
            <th className="px-3 py-2 text-right">Prob.</th>
            <th className="px-3 py-2 text-right">AI</th>
          </tr>
        </thead>
        <tbody>
          {dashboard.top_deals.map((d) => (
            <tr key={d.id} className="border-t border-slate-100">
              <td className="px-3 py-2 font-medium text-slate-800">
                {d.title}
                <div className="text-[10px] text-slate-500">
                  {d.customer?.full_name ?? "—"}
                </div>
              </td>
              <td className="px-3 py-2 text-xs text-slate-600">{d.stage}</td>
              <td className="px-3 py-2 text-right font-mono text-xs">
                {Number(d.estimated_value).toLocaleString("es-ES", {
                  style: "currency",
                  currency: "USD",
                  maximumFractionDigits: 0
                })}
              </td>
              <td className="px-3 py-2 text-right text-xs">{d.probability}%</td>
              <td className="px-3 py-2 text-right text-xs font-semibold text-indigo-600">
                {d.ai_score?.total ?? "—"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function ReportingDashboard() {
  return (
    <div className="space-y-4 overflow-y-auto pb-4">
      <section>
        <h3 className="mb-2 text-sm font-semibold text-slate-700">
          Métricas clave
        </h3>
        <MetricsView />
      </section>
      <section>
        <h3 className="mb-2 text-sm font-semibold text-slate-700">
          Embudo de ventas
        </h3>
        <FunnelView />
      </section>
      <section>
        <h3 className="mb-2 text-sm font-semibold text-slate-700">
          Distribución
        </h3>
        <BreakdownsView />
      </section>
      <section>
        <h3 className="mb-2 text-sm font-semibold text-slate-700">
          Top deals por AI score
        </h3>
        <TopDealsView />
      </section>
    </div>
  );
}
