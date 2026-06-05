"use client";

import {
  ArrowRight,
  Crown,
  Flame,
  Lightbulb,
  Package,
  Sparkles,
  Target
} from "lucide-react";
import Link from "next/link";
import type { LucideIcon } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import type {
  ExecutiveDashboardRecommendation,
  ExecutiveDashboardRecommendationPriority
} from "@/types/executive-dashboard";
import { cn } from "@/lib/utils";

type AiRecommendationsPanelProps = {
  recommendations: ExecutiveDashboardRecommendation[];
  isLoading: boolean;
};

const priorityDot: Record<ExecutiveDashboardRecommendationPriority, string> = {
  high: "bg-rose-500",
  medium: "bg-amber-500",
  low: "bg-blue-500",
};

const priorityLabel: Record<ExecutiveDashboardRecommendationPriority, string> = {
  high: "Alta",
  medium: "Media",
  low: "Baja",
};

const categoryIcon: Record<string, LucideIcon> = {
  lead_caliente: Flame,
  vip_inactivo: Crown,
  upsell: Target,
  producto_top: Package,
  default: Lightbulb,
};

function iconForCategory(category: string): LucideIcon {
  return categoryIcon[category] ?? categoryIcon.default;
}

function scoreTone(score: number) {
  if (score >= 75) return "bg-emerald-50 text-emerald-700";
  if (score >= 50) return "bg-amber-50 text-amber-700";
  return "bg-slate-100 text-slate-600";
}

export function AiRecommendationsPanel({ recommendations, isLoading }: AiRecommendationsPanelProps) {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10 text-primary">
            <Sparkles className="h-4 w-4" />
          </div>
          <div>
            <CardTitle className="text-sm">Recomendaciones de la IA comercial</CardTitle>
            <p className="text-xs text-muted-foreground">
              Acciones priorizadas para mover el negocio esta semana.
            </p>
          </div>
          <span className="ml-auto rounded-full bg-secondary px-2 py-0.5 text-xs font-medium text-muted-foreground">
            {recommendations.length}
          </span>
        </div>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="grid gap-3 lg:grid-cols-2">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="rounded-lg border p-4">
                <Skeleton className="h-4 w-32" />
                <Skeleton className="mt-3 h-12 w-full" />
                <Skeleton className="mt-3 h-8 w-24" />
              </div>
            ))}
          </div>
        ) : recommendations.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            La IA no tiene recomendaciones activas por ahora. Vuelve a revisar más tarde.
          </p>
        ) : (
          <ul className="grid gap-3 lg:grid-cols-2">
            {recommendations.map((rec) => {
              const Icon = iconForCategory(rec.category);
              return (
                <li
                  key={rec.id}
                  className="group flex flex-col gap-3 rounded-lg border bg-background p-4 transition-colors hover:border-primary/40 hover:bg-secondary/40"
                >
                  <div className="flex items-start gap-3">
                    <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
                      <Icon className="h-4 w-4" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="flex items-start justify-between gap-2">
                        <h4 className="text-sm font-semibold text-foreground">{rec.title}</h4>
                        <span
                          className={cn(
                            "shrink-0 rounded-md px-2 py-0.5 text-[11px] font-semibold",
                            scoreTone(rec.score)
                          )}
                        >
                          {rec.score}
                        </span>
                      </div>
                      <p className="mt-1 text-xs leading-5 text-muted-foreground">
                        {rec.description}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center justify-between gap-2 border-t pt-3">
                    <span className="inline-flex items-center gap-1.5 text-[11px] font-medium text-muted-foreground">
                      <span className={cn("h-2 w-2 rounded-full", priorityDot[rec.priority])} />
                      Prioridad {priorityLabel[rec.priority]}
                    </span>
                    {rec.cta_href ? (
                      <Link
                        href={rec.cta_href}
                        className="inline-flex items-center gap-1 rounded-md bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground transition-colors hover:bg-primary/90"
                      >
                        {rec.cta_label}
                        <ArrowRight className="h-3 w-3" />
                      </Link>
                    ) : (
                      <span className="inline-flex items-center gap-1 rounded-md bg-secondary px-3 py-1.5 text-xs font-medium text-muted-foreground">
                        {rec.cta_label}
                      </span>
                    )}
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}
