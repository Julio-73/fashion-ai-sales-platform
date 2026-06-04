"use client";

import { useState } from "react";
import { LayoutGrid, Plus, TrendingUp } from "lucide-react";

import { Button } from "@/components/ui/button";
import { usePipelineStore } from "@/store/pipeline-store";

import { KanbanBoard } from "./kanban-board";
import { NewDealDialog } from "./new-deal-dialog";
import { ReportingDashboard } from "./reporting-dashboard";

type Tab = "kanban" | "dashboard";

export function PipelineDashboard() {
  const store = usePipelineStore();
  const [tab, setTab] = useState<Tab>("kanban");
  const [showNew, setShowNew] = useState(false);

  return (
    <div className="flex h-full flex-col gap-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-1 rounded-lg border border-slate-200 bg-white p-0.5">
          <button
            type="button"
            onClick={() => setTab("kanban")}
            className={`flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium ${
              tab === "kanban"
                ? "bg-indigo-600 text-white"
                : "text-slate-600 hover:bg-slate-50"
            }`}
          >
            <LayoutGrid className="h-3.5 w-3.5" />
            Kanban
          </button>
          <button
            type="button"
            onClick={() => setTab("dashboard")}
            className={`flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium ${
              tab === "dashboard"
                ? "bg-indigo-600 text-white"
                : "text-slate-600 hover:bg-slate-50"
            }`}
          >
            <TrendingUp className="h-3.5 w-3.5" />
            Reportes
          </button>
        </div>
        <Button onClick={() => setShowNew(true)} disabled={store.isMutating}>
          <Plus className="mr-1.5 h-3.5 w-3.5" />
          Nuevo deal
        </Button>
      </div>

      <div className="flex-1">
        {tab === "kanban" ? <KanbanBoard /> : <ReportingDashboard />}
      </div>

      {showNew ? <NewDealDialog onClose={() => setShowNew(false)} /> : null}
    </div>
  );
}
