"use client";

import { motion } from "framer-motion";
import {
  ArrowRight,
  Crown,
  Flame,
  Lightbulb,
  Package,
  Sparkles,
  Target,
  type LucideIcon
} from "lucide-react";
import Link from "next/link";

import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { StatusPill } from "@/components/ui/status-pill";
import type {
  ExecutiveDashboardRecommendation,
  ExecutiveDashboardRecommendationPriority
} from "@/types/executive-dashboard";
import { cn } from "@/lib/utils";

type AiRecommendationsPanelProps = {
  recommendations: ExecutiveDashboardRecommendation[];
  isLoading: boolean;
};

const priorityTone: Record<
  ExecutiveDashboardRecommendationPriority,
  "destructive" | "warning" | "info"
> = {
  high: "destructive",
  medium: "warning",
  low: "info"
};

const priorityLabel: Record<ExecutiveDashboardRecommendationPriority, string> = {
  high: "Alta",
  medium: "Media",
  low: "Baja"
};

const categoryIcon: Record<string, LucideIcon> = {
  lead_caliente: Flame,
  vip_inactivo: Crown,
  upsell: Target,
  producto_top: Package,
  default: Lightbulb
};

const categoryTone: Record<string, "primary" | "purple" | "success" | "warning" | "info"> = {
  lead_caliente: "warning",
  vip_inactivo: "purple",
  upsell: "success",
  producto_top: "info",
  default: "primary"
};

function iconForCategory(category: string): LucideIcon {
  return categoryIcon[category] ?? categoryIcon.default;
}

export function AiRecommendationsPanel({
  recommendations,
  isLoading
}: AiRecommendationsPanelProps) {
  return (
    <Card variant="elevated">
      <CardContent>
        <div className="mb-5 flex items-center gap-3">
          <div className="relative flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-primary-100 to-primary-50 text-primary ring-1 ring-primary-200/60">
            <Sparkles className="h-4 w-4" aria-hidden="true" />
            <span
              aria-hidden="true"
              className="absolute -right-0.5 -top-0.5 h-2.5 w-2.5 animate-pulse-soft rounded-full bg-primary ring-2 ring-card"
            />
          </div>
          <div className="min-w-0 flex-1">
            <h3 className="text-sm font-semibold tracking-tight">
              Recomendaciones de la IA comercial
            </h3>
            <p className="mt-0.5 text-xs text-muted-foreground">
              Acciones priorizadas para mover el negocio esta semana.
            </p>
          </div>
          <span className="rounded-full bg-primary-50 px-2.5 py-0.5 text-xs font-semibold text-primary-700 ring-1 ring-inset ring-primary-200 dark:bg-primary-50/20 dark:text-primary-300 dark:ring-primary-300/30">
            {recommendations.length} activas
          </span>
        </div>

        {isLoading ? (
          <div className="grid gap-3 lg:grid-cols-2">
            {Array.from({ length: 4 }).map((_, i) => (
              <div
                key={i}
                className="rounded-xl border bg-background p-4"
              >
                <Skeleton className="h-4 w-32" />
                <Skeleton className="mt-3 h-12 w-full" />
                <Skeleton className="mt-3 h-8 w-24" />
              </div>
            ))}
          </div>
        ) : recommendations.length === 0 ? (
          <div className="rounded-xl border border-dashed bg-muted/30 p-6 text-center text-sm text-muted-foreground">
            La IA no tiene recomendaciones activas por ahora. Vuelve a revisar más tarde.
          </div>
        ) : (
          <ul className="grid gap-3 lg:grid-cols-2">
            {recommendations.map((rec, idx) => {
              const Icon = iconForCategory(rec.category);
              const tone = categoryTone[rec.category] ?? "primary";
              const toneClass = {
                primary:
                  "bg-primary-50 text-primary ring-primary-200 dark:bg-primary-50/20 dark:text-primary-300 dark:ring-primary-300/30",
                purple:
                  "bg-purple/10 text-purple ring-purple/20 dark:bg-purple/20 dark:text-purple",
                success:
                  "bg-success-50 text-success ring-success-200 dark:bg-success-50/20 dark:text-success-200 dark:ring-success-200/30",
                warning:
                  "bg-warning-50 text-warning ring-warning-200 dark:bg-warning-50/20 dark:text-warning-200 dark:ring-warning-200/30",
                info: "bg-info-50 text-info ring-info-100 dark:bg-info-50/20 dark:text-info-200 dark:ring-info-100/30"
              }[tone];
              return (
                <motion.li
                  key={rec.id}
                  initial={{ opacity: 0, y: 6 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{
                    duration: 0.3,
                    delay: idx * 0.04,
                    ease: [0.16, 1, 0.3, 1]
                  }}
                  className="group relative flex flex-col gap-3 overflow-hidden rounded-xl border bg-background p-4 transition-all hover:border-primary-200 hover:shadow-md"
                >
                  <span
                    aria-hidden="true"
                    className="absolute inset-x-0 top-0 h-0.5 bg-gradient-to-r from-transparent via-primary-300 to-transparent opacity-0 transition-opacity group-hover:opacity-100"
                  />
                  <div className="flex items-start gap-3">
                    <div
                      className={cn(
                        "flex h-9 w-9 shrink-0 items-center justify-center rounded-lg ring-1 ring-inset",
                        toneClass
                      )}
                    >
                      <Icon className="h-4 w-4" aria-hidden="true" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="flex items-start justify-between gap-2">
                        <h4 className="text-sm font-semibold text-foreground">
                          {rec.title}
                        </h4>
                        <div className="flex shrink-0 flex-col items-end gap-0.5">
                          <span
                            className={cn(
                              "rounded-md px-2 py-0.5 text-[11px] font-semibold",
                              rec.score >= 75
                                ? "bg-success-50 text-success ring-1 ring-inset ring-success-200"
                                : rec.score >= 50
                                  ? "bg-warning-50 text-warning ring-1 ring-inset ring-warning-200"
                                  : "bg-secondary text-muted-foreground ring-1 ring-inset ring-border"
                            )}
                          >
                            {rec.score} pts
                          </span>
                          <span className="text-[10px] text-muted-foreground">
                            Score IA
                          </span>
                        </div>
                      </div>
                      <p className="mt-1 text-xs leading-5 text-muted-foreground">
                        {rec.description}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center justify-between gap-2 border-t pt-3">
                    <StatusPill tone={priorityTone[rec.priority]} dot size="sm">
                      Prioridad {priorityLabel[rec.priority]}
                    </StatusPill>
                    {rec.cta_href ? (
                      <Link
                        href={rec.cta_href}
                        className="inline-flex items-center gap-1 rounded-md bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground shadow-sm transition-all hover:bg-primary-600 hover:shadow-md active:scale-[0.98]"
                      >
                        {rec.cta_label}
                        <ArrowRight className="h-3 w-3" aria-hidden="true" />
                      </Link>
                    ) : (
                      <span className="inline-flex items-center gap-1 rounded-md bg-secondary px-3 py-1.5 text-xs font-medium text-muted-foreground">
                        {rec.cta_label}
                      </span>
                    )}
                  </div>
                </motion.li>
              );
            })}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}
