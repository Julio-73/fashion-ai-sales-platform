"use client";

import { useState } from "react";
import { Plus, X, TrendingUp, Users } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { StatusPill } from "@/components/ui/status-pill";
import { usePipelineStore } from "@/store/pipeline-store";
import { cn } from "@/lib/utils";
import { formatCurrency } from "@/modules/crm/utils/format";
import type {
  PipelineItem,
  PipelineStageInfo
} from "@/types/pipeline";

import { LeadCard } from "./lead-card";

type Props = {
  stage: PipelineStageInfo;
  deals: PipelineItem[];
  isLoading: boolean;
  draggingDeal: PipelineItem | null;
  onDragStart: (e: React.DragEvent<HTMLDivElement>, deal: PipelineItem) => void;
  onDragEnd: () => void;
  onDragOverColumn: (stageKey: string) => void;
  onDropOnColumn: (stageKey: string) => void;
  dragOverStage: string | null;
};

export function KanbanColumn({
  stage,
  deals,
  isLoading,
  draggingDeal,
  onDragStart,
  onDragEnd,
  onDragOverColumn,
  onDropOnColumn,
  dragOverStage
}: Props) {
  const store = usePipelineStore();
  const [showForm, setShowForm] = useState(false);
  const [title, setTitle] = useState("");
  const [value, setValue] = useState("0");
  const [channel, setChannel] = useState("manual");
  const [busy, setBusy] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);

  const valueCount = deals.length;
  const totalValue = deals.reduce(
    (s, d) => s + Number(d.estimated_value || 0),
    0
  );
  const avgValue = valueCount > 0 ? totalValue / valueCount : 0;
  const isOver = dragOverStage === stage.key;
  const isValidDrop =
    draggingDeal !== null &&
    draggingDeal.stage !== stage.key &&
    !stage.is_terminal;

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!title.trim()) {
      setLocalError("Título obligatorio");
      return;
    }
    setBusy(true);
    setLocalError(null);
    const created = await store.createDeal({
      title: title.trim(),
      estimated_value: Number(value) || 0,
      stage: stage.key,
      channel
    });
    setBusy(false);
    if (created) {
      setTitle("");
      setValue("0");
      setShowForm(false);
    } else {
      setLocalError("No se pudo crear el deal");
    }
  }

  return (
    <div
      data-testid={`column-${stage.key}`}
      onDragOver={(e) => {
        e.preventDefault();
        onDragOverColumn(stage.key);
      }}
      onDragLeave={() => {
        if (dragOverStage === stage.key) onDragOverColumn("");
      }}
      onDrop={(e) => {
        e.preventDefault();
        onDropOnColumn(stage.key);
      }}
      className={cn(
        "flex h-full w-72 shrink-0 flex-col rounded-2xl border bg-card/60 backdrop-blur-sm transition-all",
        isOver &&
          "border-primary border-dashed bg-primary-50 shadow-md ring-2 ring-primary-100",
        !isOver &&
          isValidDrop &&
          "ring-2 ring-primary-200 shadow-sm",
        !isOver && !isValidDrop && "shadow-xs"
      )}
    >
      <div className="rounded-t-2xl border-b border-border/60 bg-gradient-to-b from-card to-muted/40 px-3 py-2.5">
        <div className="flex items-center justify-between gap-2">
          <div className="flex min-w-0 items-center gap-2">
            <span
              className="h-2.5 w-2.5 shrink-0 rounded-full ring-2 ring-card"
              style={{ backgroundColor: stage.color }}
              aria-hidden="true"
            />
            <h3 className="truncate text-sm font-semibold tracking-tight text-foreground">
              {stage.label}
            </h3>
            <StatusPill tone="neutral" size="sm">
              {valueCount}
            </StatusPill>
          </div>
          <button
            onClick={() => setShowForm((v) => !v)}
            className="inline-flex h-7 w-7 shrink-0 items-center justify-center rounded-md text-muted-foreground transition hover:bg-primary-50 hover:text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            aria-label="Nuevo deal"
            type="button"
          >
            <Plus className="h-4 w-4" />
          </button>
        </div>
        <div className="mt-1.5 flex items-center gap-2 text-[10px] uppercase tracking-wider text-muted-foreground">
          <span className="inline-flex items-center gap-0.5">
            <TrendingUp className="h-3 w-3" aria-hidden="true" />
            {totalValue.toLocaleString("es-ES", {
              style: "currency",
              currency: "USD",
              maximumFractionDigits: 0
            })}
          </span>
          {valueCount > 0 ? (
            <span className="inline-flex items-center gap-0.5">
              <Users className="h-3 w-3" aria-hidden="true" />
              {avgValue.toLocaleString("es-ES", {
                style: "currency",
                currency: "USD",
                maximumFractionDigits: 0
              })}{" "}
              prom.
            </span>
          ) : null}
        </div>
      </div>

      {showForm ? (
        <form
          onSubmit={handleCreate}
          className="mx-3 mt-2 rounded-lg border border-border bg-card p-2 shadow-xs"
        >
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
              Nuevo deal
            </span>
            <button
              type="button"
              onClick={() => setShowForm(false)}
              className="rounded p-0.5 text-muted-foreground transition hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              aria-label="Cerrar formulario"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          </div>
          <input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Ej: pedido de pantalón negro"
            className="mt-1.5 w-full rounded-md border border-input bg-background px-2 py-1 text-xs shadow-xs placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          />
          <div className="mt-1.5 flex gap-1.5">
            <input
              type="number"
              value={value}
              onChange={(e) => setValue(e.target.value)}
              placeholder="Valor"
              className="w-1/2 rounded-md border border-input bg-background px-2 py-1 text-xs shadow-xs placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            />
            <select
              value={channel}
              onChange={(e) => setChannel(e.target.value)}
              className="w-1/2 rounded-md border border-input bg-background px-2 py-1 text-xs shadow-xs focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              <option value="manual">Manual</option>
              <option value="whatsapp">WhatsApp</option>
              <option value="web">Web</option>
              <option value="email">Email</option>
              <option value="phone">Teléfono</option>
              <option value="instagram">Instagram</option>
            </select>
          </div>
          {localError ? (
            <div className="mt-1 text-[10px] font-medium text-destructive">
              {localError}
            </div>
          ) : null}
          <Button
            type="submit"
            variant="gradient"
            size="sm"
            disabled={busy}
            className="mt-2 w-full"
          >
            {busy ? "Creando…" : "Crear deal"}
          </Button>
        </form>
      ) : null}

      <div className="flex-1 space-y-2 overflow-y-auto px-3 py-3">
        {isLoading ? (
          <>
            <Skeleton className="h-32 w-full rounded-xl" />
            <Skeleton className="h-32 w-full rounded-xl" />
          </>
        ) : null}
        {!isLoading && deals.length === 0 ? (
          <div
            className={cn(
              "rounded-xl border-2 border-dashed border-border bg-muted/30 p-4 text-center text-xs text-muted-foreground transition",
              isOver && "border-primary bg-primary-50/40 text-primary"
            )}
          >
            {isOver ? "Suelta aquí" : "Suelta un deal aquí"}
          </div>
        ) : null}
        {deals.map((d) => (
          <LeadCard
            key={d.id}
            deal={d}
            isDragging={draggingDeal?.id === d.id}
            onDragStart={onDragStart}
            onDragEnd={onDragEnd}
          />
        ))}
      </div>

      {valueCount > 0 ? (
        <div className="border-t border-border/60 bg-muted/30 px-3 py-1.5 text-[10px] text-muted-foreground">
          {stage.is_terminal ? "Etapa terminal" : `Prob. base ${stage.default_probability}%`}
        </div>
      ) : null}
    </div>
  );
}
