"use client";

import { Clock, MessageSquare, RefreshCw, UserRound } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { t } from "@/lib/i18n";
import type { ActivityEvent } from "@/types/sales";
import { cn } from "@/lib/utils";

const S = t.sales.activity;

type SalesActivityTimelineProps = {
  events: ActivityEvent[];
  isLoading: boolean;
  error: string | null;
  onSelectCustomer: (customerId: string) => void;
};

const eventIcon: Record<string, typeof MessageSquare> = {
  message: MessageSquare,
  conversation: RefreshCw,
  status_change: RefreshCw,
};

const eventLabel: Record<string, string> = {
  message: S.message,
  conversation: S.conversation,
  status_change: S.statusChange,
};

function formatTimestamp(ts: string): string {
  const d = new Date(ts);
  const now = new Date();
  const diffMs = now.getTime() - d.getTime();
  const mins = Math.floor(diffMs / (1000 * 60));
  if (mins < 1) return "Ahora";
  if (mins < 60) return `Hace ${mins} min`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `Hace ${hours}h`;
  const days = Math.floor(hours / 24);
  if (days === 1) return "Ayer";
  if (days < 7) return `Hace ${days} días`;
  return d.toLocaleDateString("es-ES", { day: "numeric", month: "short" });
}

export function SalesActivityTimeline({ events, isLoading, error, onSelectCustomer }: SalesActivityTimelineProps) {
  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">{S.title}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="rounded-lg border border-destructive/25 bg-destructive/10 px-4 py-3 text-sm text-destructive">{error}</div>
        </CardContent>
      </Card>
    );
  }

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">{S.title}</CardTitle>
          <Skeleton className="h-3 w-40" />
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="flex gap-3">
                <Skeleton className="h-8 w-8 rounded-full" />
                <div className="flex-1">
                  <Skeleton className="h-4 w-40" />
                  <Skeleton className="mt-1 h-3 w-24" />
                </div>
              </div>
            ))}
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
        {events.length === 0 ? (
          <div className="flex flex-col items-center gap-2 py-8 text-center">
            <Clock className="h-8 w-8 text-muted-foreground/50" />
            <p className="text-sm font-medium text-muted-foreground">{S.noActivity}</p>
            <p className="text-xs text-muted-foreground/70">{S.noActivityDesc}</p>
          </div>
        ) : (
          <div className="relative space-y-0">
            {events.map((event, i) => {
              const Icon = eventIcon[event.event_type] ?? MessageSquare;
              const label = eventLabel[event.event_type] ?? event.event_type;
              return (
                <div
                  key={`${event.timestamp}-${i}`}
                  className="relative flex gap-4 pb-6 last:pb-0"
                >
                  {i < events.length - 1 && (
                    <div className="absolute left-4 top-10 h-full w-px bg-border" />
                  )}
                  <div className={cn(
                    "flex h-8 w-8 shrink-0 items-center justify-center rounded-full border",
                    event.event_type === "message" ? "bg-blue-50 border-blue-200" :
                    event.event_type === "conversation" ? "bg-amber-50 border-amber-200" :
                    "bg-slate-50 border-slate-200"
                  )}>
                    <Icon className={cn(
                      "h-4 w-4",
                      event.event_type === "message" ? "text-blue-600" :
                      event.event_type === "conversation" ? "text-amber-600" :
                      "text-slate-600"
                    )} />
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      {event.customer_name ? (
                        <button
                          type="button"
                          className="truncate text-sm font-medium hover:text-primary"
                          onClick={() => onSelectCustomer(event.customer_id)}
                        >
                          {event.customer_name}
                        </button>
                      ) : (
                        <UserRound className="h-4 w-4 text-muted-foreground" />
                      )}
                      <span className="shrink-0 text-xs text-muted-foreground">{label}</span>
                    </div>
                    <p className="mt-0.5 line-clamp-2 text-xs text-muted-foreground">{event.description}</p>
                    <p className="mt-0.5 text-[11px] text-muted-foreground/60">{formatTimestamp(event.timestamp)}</p>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
