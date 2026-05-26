"use client";

import { MoreHorizontal } from "lucide-react";
import { useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { StatusBadge } from "@/components/ui/status-badge";
import { t } from "@/lib/i18n";
import type { ConversionProbability, CustomerPriority, LeadStatus, TopLead } from "@/types/sales";
import { cn } from "@/lib/utils";

const S = t.sales.topLeads;

type SortKey = "lead_score" | "full_name" | "lead_status" | "priority" | "conversion_probability";

type TopLeadsTableProps = {
  leads: TopLead[];
  isLoading: boolean;
  error: string | null;
  onSelectCustomer: (customerId: string) => void;
};

const statusConfig: Record<LeadStatus, { tone: "success" | "warning" | "neutral"; label: string }> = {
  new: { tone: "neutral", label: "Nuevo" },
  interested: { tone: "warning", label: "Interesado" },
  negotiating: { tone: "warning", label: "Negociando" },
  won: { tone: "success", label: "Ganado" },
  lost: { tone: "neutral", label: "Perdido" },
};

const priorityConfig: Record<CustomerPriority, { class: string; label: string }> = {
  hot: { class: "bg-red-50 text-red-700 ring-red-200", label: "Caliente" },
  warm: { class: "bg-orange-50 text-orange-700 ring-orange-200", label: "Cálido" },
  cool: { class: "bg-blue-50 text-blue-700 ring-blue-200", label: "Frío" },
  cold: { class: "bg-slate-100 text-slate-700 ring-slate-200", label: "Helado" },
};

const probabilityConfig: Record<ConversionProbability, { class: string; label: string }> = {
  high: { class: "bg-emerald-50 text-emerald-700", label: "Alta" },
  medium: { class: "bg-amber-50 text-amber-700", label: "Media" },
  low: { class: "bg-slate-100 text-slate-500", label: "Baja" },
};

function formatDate(dateStr: string | null): string {
  if (!dateStr) return "—";
  const d = new Date(dateStr);
  const now = new Date();
  const diff = now.getTime() - d.getTime();
  const days = Math.floor(diff / (1000 * 60 * 60 * 24));
  if (days === 0) return "Hoy";
  if (days === 1) return "Ayer";
  if (days < 7) return `Hace ${days} días`;
  return d.toLocaleDateString("es-ES", { day: "numeric", month: "short" });
}

export function TopLeadsTable({ leads, isLoading, error, onSelectCustomer }: TopLeadsTableProps) {
  const [sortKey, setSortKey] = useState<SortKey>("lead_score");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");

  const sorted = useMemo(() => {
    return [...leads].sort((a, b) => {
      const aVal = a[sortKey];
      const bVal = b[sortKey];
      if (typeof aVal === "string" && typeof bVal === "string") {
        return sortDir === "desc" ? bVal.localeCompare(aVal) : aVal.localeCompare(bVal);
      }
      return sortDir === "desc" ? (bVal as number) - (aVal as number) : (aVal as number) - (bVal as number);
    });
  }, [leads, sortKey, sortDir]);

  function toggleSort(key: SortKey) {
    if (sortKey === key) {
      setSortDir((d) => (d === "desc" ? "asc" : "desc"));
    } else {
      setSortKey(key);
      setSortDir("desc");
    }
  }

  const sortIndicator = (key: SortKey) => {
    if (sortKey !== key) return null;
    return <span className="ml-1 text-[10px]">{sortDir === "desc" ? "▼" : "▲"}</span>;
  };

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">{S.title}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="rounded-lg border border-destructive/25 bg-destructive/10 px-4 py-3 text-sm text-destructive">
            {error}
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm">{S.title}</CardTitle>
        <p className="text-xs text-muted-foreground">{S.description}</p>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="space-y-3">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="flex items-center gap-4">
                <Skeleton className="h-5 w-32" />
                <Skeleton className="h-5 w-12" />
                <Skeleton className="h-5 w-20" />
                <Skeleton className="h-5 w-16" />
              </div>
            ))}
          </div>
        ) : sorted.length === 0 ? (
          <div className="flex flex-col items-center gap-2 py-8 text-center">
            <MoreHorizontal className="h-8 w-8 text-muted-foreground/50" />
            <p className="text-sm font-medium text-muted-foreground">{S.emptyTitle}</p>
            <p className="text-xs text-muted-foreground/70">{S.emptyDesc}</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-left text-xs uppercase tracking-wide text-muted-foreground">
                  <th className="cursor-pointer pb-3 pr-4 font-medium hover:text-foreground" onClick={() => toggleSort("full_name")}>
                    {S.name}{sortIndicator("full_name")}
                  </th>
                  <th className="cursor-pointer pb-3 pr-4 font-medium hover:text-foreground" onClick={() => toggleSort("lead_score")}>
                    {S.score}{sortIndicator("lead_score")}
                  </th>
                  <th className="cursor-pointer pb-3 pr-4 font-medium hover:text-foreground" onClick={() => toggleSort("lead_status")}>
                    {S.status}{sortIndicator("lead_status")}
                  </th>
                  <th className="cursor-pointer pb-3 pr-4 font-medium hover:text-foreground" onClick={() => toggleSort("priority")}>
                    {S.priority}{sortIndicator("priority")}
                  </th>
                  <th className="hidden pb-3 pr-4 font-medium md:table-cell">{S.activity}</th>
                  <th className="hidden pb-3 pr-4 font-medium lg:table-cell">{S.lastInteraction}</th>
                  <th className="cursor-pointer pb-3 font-medium hover:text-foreground" onClick={() => toggleSort("conversion_probability")}>
                    {S.probability}{sortIndicator("conversion_probability")}
                  </th>
                </tr>
              </thead>
              <tbody>
                {sorted.map((lead) => (
                  <tr
                    key={lead.customer_id}
                    className="cursor-pointer border-b last:border-0 hover:bg-muted/50"
                    onClick={() => onSelectCustomer(lead.customer_id)}
                  >
                    <td className="py-3 pr-4 font-medium">{lead.full_name}</td>
                    <td className="py-3 pr-4">
                      <span className={cn(
                        "inline-flex min-w-[2rem] items-center justify-center rounded-md px-2 py-0.5 text-xs font-semibold",
                        lead.lead_score >= 60 ? "bg-emerald-50 text-emerald-700" :
                        lead.lead_score >= 20 ? "bg-amber-50 text-amber-700" :
                        "bg-slate-100 text-slate-500"
                      )}>
                        {lead.lead_score}
                      </span>
                    </td>
                    <td className="py-3 pr-4">
                      <StatusBadge tone={statusConfig[lead.lead_status]?.tone ?? "neutral"}>
                        {statusConfig[lead.lead_status]?.label ?? lead.lead_status}
                      </StatusBadge>
                    </td>
                    <td className="py-3 pr-4">
                      <span className={cn(
                        "inline-flex rounded-md px-2 py-0.5 text-xs font-medium ring-1",
                        priorityConfig[lead.priority]?.class ?? "bg-slate-100 text-slate-700 ring-slate-200"
                      )}>
                        {priorityConfig[lead.priority]?.label ?? lead.priority}
                      </span>
                    </td>
                    <td className="hidden py-3 pr-4 text-muted-foreground md:table-cell">
                      {lead.conversation_count > 0 ? `${lead.conversation_count} conv.` : "Sin actividad"}
                    </td>
                    <td className="hidden py-3 pr-4 text-muted-foreground lg:table-cell">
                      {formatDate(lead.last_interaction_at)}
                    </td>
                    <td className="py-3">
                      <span className={cn(
                        "inline-flex rounded-md px-2 py-0.5 text-xs font-medium",
                        probabilityConfig[lead.conversion_probability]?.class ?? "bg-slate-100 text-slate-500"
                      )}>
                        {probabilityConfig[lead.conversion_probability]?.label ?? lead.conversion_probability}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
