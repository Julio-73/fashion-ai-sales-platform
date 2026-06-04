"use client";

import { useState } from "react";
import { Plus, X } from "lucide-react";

import { Button } from "@/components/ui/button";
import { usePipelineStore } from "@/store/pipeline-store";
import type { PipelineChannel, PipelineStageKey } from "@/types/pipeline";

type Props = {
  onClose: () => void;
};

const CHANNELS: Array<{ value: PipelineChannel; label: string }> = [
  { value: "whatsapp", label: "WhatsApp" },
  { value: "web", label: "Web" },
  { value: "email", label: "Email" },
  { value: "phone", label: "Teléfono" },
  { value: "instagram", label: "Instagram" },
  { value: "manual", label: "Manual" }
];

export function NewDealDialog({ onClose }: Props) {
  const store = usePipelineStore();
  const [title, setTitle] = useState("");
  const [value, setValue] = useState("0");
  const [probability, setProbability] = useState("20");
  const [stage, setStage] = useState<PipelineStageKey>("new_lead");
  const [channel, setChannel] = useState<PipelineChannel>("manual");
  const [isVip, setIsVip] = useState(false);
  const [notes, setNotes] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!title.trim()) {
      setErr("El título es obligatorio");
      return;
    }
    setBusy(true);
    setErr(null);
    const created = await store.createDeal({
      title: title.trim(),
      estimated_value: Number(value) || 0,
      probability: Math.min(100, Math.max(0, Number(probability) || 0)),
      stage,
      channel,
      is_vip: isVip,
      notes: notes.trim() || undefined
    });
    setBusy(false);
    if (created) {
      onClose();
    } else {
      setErr("No se pudo crear el deal");
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 p-4">
      <form
        onSubmit={handleSubmit}
        className="w-full max-w-md rounded-xl bg-white p-4 shadow-xl"
      >
        <div className="mb-3 flex items-center justify-between">
          <h3 className="text-base font-semibold text-slate-800">
            Nuevo deal
          </h3>
          <button
            type="button"
            onClick={onClose}
            className="rounded p-1 text-slate-400 hover:text-slate-600"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="space-y-2.5">
          <div>
            <label className="text-[11px] font-medium text-slate-600">
              Título
            </label>
            <input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
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
          <div className="grid grid-cols-2 gap-2.5">
            <div>
              <label className="text-[11px] font-medium text-slate-600">
                Etapa inicial
              </label>
              <select
                value={stage}
                onChange={(e) => setStage(e.target.value as PipelineStageKey)}
                className="mt-0.5 w-full rounded-lg border border-slate-200 px-2.5 py-1.5 text-sm focus:border-indigo-400 focus:outline-none"
              >
                {store.stages
                  .filter((s) => s.is_open)
                  .map((s) => (
                    <option key={s.key} value={s.key}>
                      {s.label}
                    </option>
                  ))}
              </select>
            </div>
            <div>
              <label className="text-[11px] font-medium text-slate-600">
                Canal
              </label>
              <select
                value={channel}
                onChange={(e) => setChannel(e.target.value as PipelineChannel)}
                className="mt-0.5 w-full rounded-lg border border-slate-200 px-2.5 py-1.5 text-sm focus:border-indigo-400 focus:outline-none"
              >
                {CHANNELS.map((c) => (
                  <option key={c.value} value={c.value}>
                    {c.label}
                  </option>
                ))}
              </select>
            </div>
          </div>
          <div>
            <label className="text-[11px] font-medium text-slate-600">
              Notas
            </label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={3}
              className="mt-0.5 w-full rounded-lg border border-slate-200 px-2.5 py-1.5 text-sm focus:border-indigo-400 focus:outline-none"
            />
          </div>
          <label className="flex items-center gap-2 text-xs text-slate-700">
            <input
              type="checkbox"
              checked={isVip}
              onChange={(e) => setIsVip(e.target.checked)}
              className="h-4 w-4 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
            />
            Marcar como VIP
          </label>
          {err ? <div className="text-xs text-rose-600">{err}</div> : null}
        </div>

        <div className="mt-4 flex justify-end gap-2">
          <Button type="button" variant="ghost" onClick={onClose}>
            Cancelar
          </Button>
          <Button type="submit" disabled={busy}>
            <Plus className="mr-1.5 h-3.5 w-3.5" />
            {busy ? "Creando…" : "Crear deal"}
          </Button>
        </div>
      </form>
    </div>
  );
}
