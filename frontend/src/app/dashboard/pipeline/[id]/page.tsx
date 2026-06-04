"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import {
  ArrowLeft,
  ChevronRight,
  Crown,
  Flame,
  Mail,
  MessageCircle,
  Phone,
  Save,
  Sparkles,
  Trash2,
  TrendingUp,
  User as UserIcon,
  Webhook
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { AppShell } from "@/components/layout/app-shell";
import { DashboardContent } from "@/components/layout/dashboard-content";
import { DashboardHeader } from "@/components/layout/dashboard-header";
import { EmptyState } from "@/components/feedback/empty-state";
import { ApiError } from "@/services/api-client";
import * as pipelineService from "@/services/pipeline.service";
import { useAuthStore } from "@/store/auth-store";
import {
  PipelineStoreProvider,
  usePipelineStore
} from "@/store/pipeline-store";
import type { PipelineStageKey } from "@/types/pipeline";
import { formatCurrency } from "@/modules/crm/utils/format";

const CHANNEL_ICON: Record<string, typeof MessageCircle> = {
  whatsapp: MessageCircle,
  email: Mail,
  web: Webhook,
  phone: Phone,
  instagram: MessageCircle,
  manual: UserIcon
};

function ScoreRing({ value }: { value: number }) {
  const safe = Math.max(0, Math.min(100, value));
  const stroke = safe >= 75 ? "#10b981" : safe >= 45 ? "#f59e0b" : "#94a3b8";
  const r = 32;
  const c = 2 * Math.PI * r;
  const offset = c * (1 - safe / 100);
  return (
    <svg width="80" height="80" viewBox="0 0 80 80">
      <circle
        cx="40"
        cy="40"
        r={r}
        stroke="#e2e8f0"
        strokeWidth="6"
        fill="none"
      />
      <circle
        cx="40"
        cy="40"
        r={r}
        stroke={stroke}
        strokeWidth="6"
        fill="none"
        strokeLinecap="round"
        strokeDasharray={c}
        strokeDashoffset={offset}
        transform="rotate(-90 40 40)"
      />
      <text
        x="40"
        y="44"
        textAnchor="middle"
        fontSize="16"
        fontWeight="700"
        fill="#1e293b"
      >
        {safe}
      </text>
    </svg>
  );
}

function DealDetail() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const { accessToken, refreshSession } = useAuthStore();
  const store = usePipelineStore();
  const [deal, setDeal] = useState<Awaited<
    ReturnType<typeof pipelineService.getDeal>
  > | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);
  const [title, setTitle] = useState("");
  const [value, setValue] = useState("");
  const [probability, setProbability] = useState("");
  const [notes, setNotes] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [savedAt, setSavedAt] = useState<string | null>(null);

  useEffect(() => {
    if (!accessToken || !params?.id) return;
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [accessToken, params?.id]);

  async function load(retried = false) {
    if (!accessToken || !params?.id) return;
    setIsLoading(true);
    setErr(null);
    try {
      const data = await pipelineService.getDeal(accessToken, params.id);
      setDeal(data);
      setTitle(data.title);
      setValue(String(data.estimated_value));
      setProbability(String(data.probability));
      setNotes(data.notes ?? "");
    } catch (e) {
      if (e instanceof ApiError && e.status === 404) {
        setNotFound(true);
        return;
      }
      if (!retried && e instanceof ApiError && e.status === 401) {
        try {
          await refreshSession();
          await load(true);
          return;
        } catch {
          /* ignore */
        }
      }
      if (e instanceof ApiError) setErr(e.message);
    } finally {
      setIsLoading(false);
    }
  }

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    if (!deal) return;
    setBusy(true);
    setErr(null);
    const updated = await store.updateDeal(deal.id, {
      title: title.trim(),
      estimated_value: Number(value) || 0,
      probability: Math.min(100, Math.max(0, Number(probability) || 0)),
      notes: notes
    });
    setBusy(false);
    if (updated) {
      setDeal(updated);
      setSavedAt(new Date().toLocaleTimeString("es-PE"));
    } else {
      setErr("No se pudo guardar");
    }
  }

  async function handleMove(targetStage: PipelineStageKey) {
    if (!deal) return;
    const target = store.stages.find((s) => s.key === targetStage);
    const probability = target?.default_probability ?? deal.probability;
    const extras: Record<string, string> = {};
    if (targetStage === "won") extras.won_reason = notes || "Cierre estándar";
    if (targetStage === "lost") extras.lost_reason = notes || "Sin respuesta";
    const moved = await store.moveStage(deal.id, targetStage, {
      probability,
      ...extras
    });
    if (moved) setDeal(moved);
  }

  async function handleDelete() {
    if (!deal) return;
    if (!window.confirm("¿Eliminar este deal? Esta acción no se puede deshacer."))
      return;
    const ok = await store.deleteDeal(deal.id);
    if (ok) router.push("/dashboard/pipeline");
  }

  if (isLoading) {
    return (
      <div className="space-y-3">
        <Skeleton className="h-8 w-1/3" />
        <Skeleton className="h-32 w-full" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (notFound || !deal) {
    return (
      <EmptyState
        title="Deal no encontrado"
        description="Es posible que haya sido eliminado o que no tengas acceso."
        action={{
          label: "Volver al pipeline",
          onClick: () => router.push("/dashboard/pipeline")
        }}
      />
    );
  }

  const ChannelIcon = CHANNEL_ICON[deal.channel ?? "manual"] ?? UserIcon;
  const aiScore = deal.ai_score;
  const currentStage = store.stages.find((s) => s.key === deal.stage);
  const openStages = store.stages.filter((s) => s.is_open);

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 text-sm">
        <Link
          href="/dashboard/pipeline"
          className="flex items-center gap-1 text-slate-500 hover:text-indigo-600"
        >
          <ArrowLeft className="h-3.5 w-3.5" /> Pipeline
        </Link>
        <ChevronRight className="h-3.5 w-3.5 text-slate-300" />
        <span className="font-medium text-slate-800">{deal.title}</span>
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Información del deal</CardTitle>
            {deal.is_vip ? (
              <span className="flex items-center gap-1 rounded-full bg-amber-50 px-2 py-0.5 text-xs font-semibold text-amber-700">
                <Crown className="h-3 w-3" /> VIP
              </span>
            ) : null}
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSave} className="space-y-3">
              <div>
                <label className="text-[11px] font-medium text-slate-600">
                  Título
                </label>
                <input
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="mt-0.5 w-full rounded-lg border border-slate-200 px-2.5 py-1.5 text-sm focus:border-indigo-400 focus:outline-none"
                />
              </div>
              <div className="grid grid-cols-2 gap-2.5">
                <div>
                  <label className="text-[11px] font-medium text-slate-600">
                    Valor estimado
                  </label>
                  <input
                    type="number"
                    value={value}
                    onChange={(e) => setValue(e.target.value)}
                    className="mt-0.5 w-full rounded-lg border border-slate-200 px-2.5 py-1.5 text-sm focus:border-indigo-400 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="text-[11px] font-medium text-slate-600">
                    Probabilidad %
                  </label>
                  <input
                    type="number"
                    min={0}
                    max={100}
                    value={probability}
                    onChange={(e) => setProbability(e.target.value)}
                    className="mt-0.5 w-full rounded-lg border border-slate-200 px-2.5 py-1.5 text-sm focus:border-indigo-400 focus:outline-none"
                  />
                </div>
              </div>
              <div>
                <label className="text-[11px] font-medium text-slate-600">
                  Notas
                </label>
                <textarea
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  rows={4}
                  className="mt-0.5 w-full rounded-lg border border-slate-200 px-2.5 py-1.5 text-sm focus:border-indigo-400 focus:outline-none"
                />
              </div>
              <div className="flex items-center justify-between">
                <div>
                  {err ? (
                    <span className="text-xs text-rose-600">{err}</span>
                  ) : savedAt ? (
                    <span className="text-xs text-emerald-600">
                      Guardado a las {savedAt}
                    </span>
                  ) : null}
                </div>
                <div className="flex gap-2">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={handleDelete}
                    disabled={busy}
                  >
                    <Trash2 className="mr-1.5 h-3.5 w-3.5 text-rose-500" />
                    Eliminar
                  </Button>
                  <Button type="submit" disabled={busy}>
                    <Save className="mr-1.5 h-3.5 w-3.5" />
                    {busy ? "Guardando…" : "Guardar"}
                  </Button>
                </div>
              </div>
            </form>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-amber-500" /> IA Comercial
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-3">
              <ScoreRing value={aiScore?.total ?? 0} />
              <div className="text-xs text-slate-600">
                <div>
                  <strong>{aiScore?.total ?? "—"}/100</strong> score global
                </div>
                <div className="mt-0.5 text-slate-500">
                  Intención {aiScore?.intent ?? "—"} · Engagement{" "}
                  {aiScore?.engagement ?? "—"} · Recencia {aiScore?.recency ?? "—"}
                </div>
                <div className="mt-0.5 text-slate-500">
                  Valor {aiScore?.monetary ?? "—"} · Sentimiento{" "}
                  {aiScore?.sentiment ?? "—"}
                </div>
              </div>
            </div>
            {aiScore?.rationale && aiScore.rationale.length > 0 ? (
              <ul className="mt-3 space-y-1.5 text-xs text-slate-700">
                {aiScore.rationale.map((r, i) => (
                  <li key={i} className="flex gap-1.5">
                    <span className="text-indigo-500">•</span>
                    {r}
                  </li>
                ))}
              </ul>
            ) : (
              <div className="mt-3 text-xs text-slate-400">
                Sin señales relevantes. Vuelve cuando haya más datos del
                cliente.
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Cliente</CardTitle>
          </CardHeader>
          <CardContent className="text-sm">
            {deal.customer ? (
              <div className="space-y-1.5">
                <div className="flex items-center gap-2">
                  <div className="flex h-8 w-8 items-center justify-center rounded-full bg-indigo-100 text-xs font-bold text-indigo-600">
                    {deal.customer.full_name
                      .split(" ")
                      .map((p) => p[0])
                      .slice(0, 2)
                      .join("")
                      .toUpperCase()}
                  </div>
                  <div>
                    <div className="font-medium text-slate-800">
                      {deal.customer.full_name}
                    </div>
                    <Link
                      href={`/dashboard/customers/${deal.customer.id}`}
                      className="text-[11px] text-indigo-600 hover:underline"
                    >
                      Ver customer 360 →
                    </Link>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-1.5 text-xs">
                  <div>
                    <div className="text-slate-500">Email</div>
                    <div className="truncate text-slate-800">
                      {deal.customer.email ?? "—"}
                    </div>
                  </div>
                  <div>
                    <div className="text-slate-500">Teléfono</div>
                    <div className="text-slate-800">
                      {deal.customer.phone ?? "—"}
                    </div>
                  </div>
                  <div>
                    <div className="text-slate-500">WhatsApp</div>
                    <div className="text-slate-800">
                      {deal.customer.whatsapp ?? "—"}
                    </div>
                  </div>
                  <div>
                    <div className="text-slate-500">Lead score</div>
                    <div className="flex items-center gap-1 text-slate-800">
                      {deal.customer.lead_score}
                      {deal.customer.priority === "hot" ? (
                        <Flame className="h-3 w-3 text-orange-500" />
                      ) : null}
                    </div>
                  </div>
                  <div>
                    <div className="text-slate-500">Pedidos</div>
                    <div className="text-slate-800">
                      {deal.customer.orders_count}
                    </div>
                  </div>
                  <div>
                    <div className="text-slate-500">LTV</div>
                    <div className="font-mono text-slate-800">
                      {formatCurrency(deal.customer.lifetime_value)}
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-xs text-slate-400">
                Sin cliente asociado
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Atributos</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-xs">
            <div className="flex items-center gap-1.5">
              <ChannelIcon className="h-3.5 w-3.5 text-slate-500" />
              <span className="text-slate-600">Canal:</span>
              <span className="font-medium capitalize text-slate-800">
                {deal.channel ?? "manual"}
              </span>
            </div>
            <div className="flex items-center gap-1.5">
              <TrendingUp className="h-3.5 w-3.5 text-slate-500" />
              <span className="text-slate-600">Etapa actual:</span>
              <span
                className="rounded-full px-2 py-0.5 font-medium"
                style={{ backgroundColor: (currentStage?.color ?? "#94a3b8") + "33" }}
              >
                {currentStage?.label ?? deal.stage}
              </span>
            </div>
            <div>
              <span className="text-slate-600">En etapa desde:</span>{" "}
              <span className="font-mono text-slate-800">
                {new Date(deal.stage_entered_at).toLocaleString("es-PE")}
              </span>
            </div>
            <div>
              <span className="text-slate-600">Última actividad:</span>{" "}
              <span className="font-mono text-slate-800">
                {new Date(deal.last_activity_at).toLocaleString("es-PE")}
              </span>
            </div>
            {deal.won_reason ? (
              <div>
                <span className="text-slate-600">Razón de cierre (won):</span>{" "}
                <span className="text-emerald-700">{deal.won_reason}</span>
              </div>
            ) : null}
            {deal.lost_reason ? (
              <div>
                <span className="text-slate-600">Razón de cierre (lost):</span>{" "}
                <span className="text-rose-700">{deal.lost_reason}</span>
              </div>
            ) : null}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Mover etapa</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-1.5">
              {openStages.map((s) => (
                <button
                  key={s.key}
                  type="button"
                  onClick={() => handleMove(s.key)}
                  disabled={s.key === deal.stage || busy}
                  className={`flex w-full items-center justify-between rounded-lg border px-2.5 py-1.5 text-left text-xs transition ${
                    s.key === deal.stage
                      ? "border-indigo-300 bg-indigo-50 text-indigo-700"
                      : "border-slate-200 bg-white text-slate-700 hover:border-indigo-300 hover:bg-indigo-50/40"
                  }`}
                >
                  <span className="flex items-center gap-1.5">
                    <span
                      className="h-2 w-2 rounded-full"
                      style={{ backgroundColor: s.color }}
                    />
                    {s.label}
                  </span>
                  <span className="text-[10px] text-slate-500">
                    {s.default_probability}%
                  </span>
                </button>
              ))}
              {store.stages
                .filter((s) => s.is_terminal)
                .map((s) => (
                  <button
                    key={s.key}
                    type="button"
                    onClick={() => handleMove(s.key)}
                    disabled={s.key === deal.stage || busy}
                    className={`flex w-full items-center justify-between rounded-lg border px-2.5 py-1.5 text-left text-xs ${
                      s.key === deal.stage
                        ? "border-slate-300 bg-slate-50 text-slate-500"
                        : "border-rose-200 bg-white text-rose-700 hover:bg-rose-50"
                    }`}
                  >
                    <span className="flex items-center gap-1.5">
                      <span
                        className="h-2 w-2 rounded-full"
                        style={{ backgroundColor: s.color }}
                      />
                      Cerrar como {s.label}
                    </span>
                  </button>
                ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export default function DealDetailPage() {
  return (
    <AppShell>
      <DashboardContent>
        <PipelineStoreProvider>
          <DashboardHeader
            eyebrow="Pipeline"
            title="Detalle del deal"
            description="Información, IA comercial y acciones de movimiento."
          />
          <DealDetail />
        </PipelineStoreProvider>
      </DashboardContent>
    </AppShell>
  );
}
