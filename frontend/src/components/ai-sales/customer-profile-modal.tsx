"use client";

import {
  Activity,
  BarChart3,
  Flame,
  Handshake,
  Heart,
  Mail,
  MessageSquare,
  Phone,
  ShoppingBag,
  Tag,
  Trophy,
  Truck,
  UserRound,
  X,
} from "lucide-react";

import { Skeleton } from "@/components/ui/skeleton";
import { StatusBadge } from "@/components/ui/status-badge";
import { t } from "@/lib/i18n";
import type { CustomerSalesProfileResponse, LeadStatus, CustomerPriority, ActivityLevel } from "@/types/sales";
import { cn } from "@/lib/utils";

const S = t.sales.profile;

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

const activityConfig: Record<ActivityLevel, { class: string; label: string }> = {
  very_active: { class: "bg-emerald-50 text-emerald-700 ring-emerald-200", label: "Muy Activo" },
  active: { class: "bg-blue-50 text-blue-700 ring-blue-200", label: "Activo" },
  moderate: { class: "bg-amber-50 text-amber-700 ring-amber-200", label: "Moderado" },
  low: { class: "bg-orange-50 text-orange-700 ring-orange-200", label: "Bajo" },
  inactive: { class: "bg-slate-100 text-slate-500 ring-slate-200", label: "Inactivo" },
};

const intentIcon: Record<string, typeof ShoppingBag> = {
  purchase_intent: ShoppingBag,
  pricing_intent: Tag,
  negotiation_intent: Handshake,
  shipping_intent: Truck,
};

const intentColor: Record<string, string> = {
  purchase_intent: "text-emerald-600 bg-emerald-50",
  pricing_intent: "text-blue-600 bg-blue-50",
  negotiation_intent: "text-amber-600 bg-amber-50",
  shipping_intent: "text-purple-600 bg-purple-50",
};

type CustomerProfileModalProps = {
  profile: CustomerSalesProfileResponse | null;
  isLoading: boolean;
  error: string | null;
  onClose: () => void;
};

export function CustomerProfileModal({ profile, isLoading, error, onClose }: CustomerProfileModalProps) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="fixed inset-0 bg-slate-950/40 backdrop-blur-sm" onClick={onClose} />
      <div className="relative z-10 max-h-[85vh] w-full max-w-lg overflow-y-auto rounded-xl border bg-card shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between border-b px-5 py-4">
          <div>
            <h2 className="text-sm font-semibold">{S.title}</h2>
            <p className="text-xs text-muted-foreground">{S.description}</p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="flex h-8 w-8 items-center justify-center rounded-md text-muted-foreground hover:bg-secondary hover:text-foreground"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="p-5">
          {isLoading ? (
            <div className="space-y-4">
              <Skeleton className="h-6 w-40" />
              <Skeleton className="h-4 w-60" />
              <div className="grid grid-cols-2 gap-3">
                {Array.from({ length: 4 }).map((_, i) => (
                  <Skeleton key={i} className="h-16 rounded-lg" />
                ))}
              </div>
              <Skeleton className="h-20 rounded-lg" />
            </div>
          ) : error ? (
            <div className="rounded-lg border border-destructive/25 bg-destructive/10 px-4 py-3 text-sm text-destructive">{error}</div>
          ) : profile ? (
            <div className="space-y-5">
              {/* Name + Contact */}
              <div>
                <div className="flex items-center gap-2">
                  <UserRound className="h-5 w-5 text-muted-foreground" />
                  <h3 className="text-base font-semibold">{profile.full_name}</h3>
                </div>
                <div className="mt-2 space-y-1 text-sm text-muted-foreground">
                  <div className="flex items-center gap-2">
                    <Mail className="h-3.5 w-3.5" />
                    <span>{profile.email}</span>
                  </div>
                  {profile.phone ? (
                    <div className="flex items-center gap-2">
                      <Phone className="h-3.5 w-3.5" />
                      <span>{profile.phone}</span>
                    </div>
                  ) : null}
                </div>
              </div>

              {/* Score + Status + Priority + Activity */}
              <div className="grid grid-cols-2 gap-3">
                <div className="rounded-lg border bg-background p-3">
                  <p className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">Score</p>
                  <p className={cn(
                    "mt-1 text-lg font-bold",
                    profile.lead_score >= 60 ? "text-emerald-600" :
                    profile.lead_score >= 20 ? "text-amber-600" :
                    "text-slate-500"
                  )}>{profile.lead_score}</p>
                </div>
                <div className="rounded-lg border bg-background p-3">
                  <p className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">Estado</p>
                  <div className="mt-1">
                    <StatusBadge tone={statusConfig[profile.lead_status]?.tone ?? "neutral"}>
                      {statusConfig[profile.lead_status]?.label ?? profile.lead_status}
                    </StatusBadge>
                  </div>
                </div>
                <div className="rounded-lg border bg-background p-3">
                  <p className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">Prioridad</p>
                  <p className={cn(
                    "mt-1 inline-flex rounded-md px-2 py-0.5 text-xs font-medium ring-1",
                    priorityConfig[profile.priority]?.class ?? "bg-slate-100 text-slate-700 ring-slate-200"
                  )}>{priorityConfig[profile.priority]?.label ?? profile.priority}</p>
                </div>
                <div className="rounded-lg border bg-background p-3">
                  <p className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">Actividad</p>
                  <p className={cn(
                    "mt-1 inline-flex rounded-md px-2 py-0.5 text-xs font-medium ring-1",
                    activityConfig[profile.activity_level]?.class ?? "bg-slate-100 text-slate-500 ring-slate-200"
                  )}>{activityConfig[profile.activity_level]?.label ?? profile.activity_level}</p>
                </div>
              </div>

              {/* Tags */}
              {profile.tags.length > 0 && (
                <div>
                  <p className="mb-2 text-xs font-medium uppercase tracking-wide text-muted-foreground">Etiquetas</p>
                  <div className="flex flex-wrap gap-1.5">
                    {profile.tags.map((tag) => (
                      <span key={tag} className="rounded-md bg-secondary px-2 py-0.5 text-xs font-medium text-secondary-foreground">
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Detected Intents */}
              {profile.detected_intents.length > 0 && (
                <div>
                  <p className="mb-2 text-xs font-medium uppercase tracking-wide text-muted-foreground">{S.intents}</p>
                  <div className="flex flex-wrap gap-1.5">
                    {profile.detected_intents.map((intent) => {
                      const Icon = intentIcon[intent] ?? BarChart3;
                      return (
                        <span key={intent} className={cn(
                          "inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-xs font-medium",
                          intentColor[intent] ?? "bg-slate-50 text-slate-600"
                        )}>
                          <Icon className="h-3 w-3" />
                          {intent.replace("_intent", "").replace("_", " ")}
                        </span>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Conversation Metrics */}
              <div>
                <p className="mb-2 text-xs font-medium uppercase tracking-wide text-muted-foreground">Conversaciones</p>
                <div className="grid grid-cols-2 gap-3">
                  <div className="flex items-center gap-2 rounded-lg border bg-background px-3 py-2">
                    <MessageSquare className="h-4 w-4 text-muted-foreground" />
                    <span className="text-sm">{profile.conversation_metrics.total_messages} {S.messages}</span>
                  </div>
                  <div className="flex items-center gap-2 rounded-lg border bg-background px-3 py-2">
                    <Activity className="h-4 w-4 text-muted-foreground" />
                    <span className="text-sm">{profile.conversation_metrics.total_conversations} {S.conversations}</span>
                  </div>
                </div>
                {profile.conversation_metrics.last_message_content && (
                  <p className="mt-2 truncate rounded-md bg-muted px-3 py-2 text-xs text-muted-foreground">
                    &ldquo;{profile.conversation_metrics.last_message_content}&rdquo;
                  </p>
                )}
              </div>

              {/* Sales Summary */}
              <div className="rounded-lg border-l-4 border-l-primary bg-primary/5 px-4 py-3">
                <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">{S.salesSummary}</p>
                <p className="mt-1 text-sm">{profile.sales_summary}</p>
              </div>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}
