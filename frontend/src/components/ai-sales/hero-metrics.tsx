"use client";

import { Flame, Heart, Handshake, Trophy } from "lucide-react";

import { t } from "@/lib/i18n";
import { MetricCard } from "@/components/ui/metric-card";
import { Skeleton } from "@/components/ui/skeleton";

const S = t.sales.hero;

type HeroMetricsProps = {
  hotLeads: number;
  interested: number;
  negotiation: number;
  converted: number;
  isLoading: boolean;
};

export function HeroMetrics({ hotLeads, interested, negotiation, converted, isLoading }: HeroMetricsProps) {
  if (isLoading) {
    return (
      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="rounded-lg border bg-card p-5">
            <Skeleton className="h-4 w-28" />
            <Skeleton className="mt-4 h-8 w-16" />
            <Skeleton className="mt-4 h-4 w-24" />
          </div>
        ))}
      </section>
    );
  }

  const metrics = [
    {
      title: S.hotLeads,
      value: String(hotLeads),
      icon: Flame,
      trend: hotLeads > 0 ? `${hotLeads} activos` : undefined,
      footer: <span className="text-xs text-muted-foreground">{S.hotLeadsDesc}</span>,
    },
    {
      title: S.interested,
      value: String(interested),
      icon: Heart,
      trend: interested > 0 ? `${interested} clientes` : undefined,
      footer: <span className="text-xs text-muted-foreground">{S.interestedDesc}</span>,
    },
    {
      title: S.negotiation,
      value: String(negotiation),
      icon: Handshake,
      trend: negotiation > 0 ? `${negotiation} activos` : undefined,
      footer: <span className="text-xs text-muted-foreground">{S.negotiationDesc}</span>,
    },
    {
      title: S.converted,
      value: String(converted),
      icon: Trophy,
      trend: converted > 0 ? `${converted} cerrados` : undefined,
      footer: <span className="text-xs text-muted-foreground">{S.convertedDesc}</span>,
    },
  ];

  return (
    <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      {metrics.map((metric, index) => (
        <MetricCard key={metric.title} {...metric} delay={index * 0.04} />
      ))}
    </section>
  );
}
