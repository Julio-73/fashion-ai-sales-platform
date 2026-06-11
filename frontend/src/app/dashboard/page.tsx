"use client";

import {
  BarChart3,
  CheckCircle2,
  Clock,
  MessageSquare,
  Package,
  Plus,
  Sparkles,
  UsersRound,
  Workflow
} from "lucide-react";
import { useRouter } from "next/navigation";
import type { ReactNode } from "react";

import { t } from "@/lib/i18n";
import { DataTable } from "@/components/data-table/data-table";
import { EmptyState } from "@/components/feedback/empty-state";
import { AppShell } from "@/components/layout/app-shell";
import { DashboardContent } from "@/components/layout/dashboard-content";
import { PageHeader } from "@/components/layout/page-header";
import { SectionHeader } from "@/components/layout/section-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { MetricCard } from "@/components/ui/metric-card";
import { StatusBadge } from "@/components/ui/status-badge";
import { StatDelta } from "@/components/ui/stat";
import { cn } from "@/lib/utils";

const D = t.dashboard.home;

const metrics = [
  {
    title: D.metricActiveCustomers,
    value: D.metricCustomersReady,
    icon: UsersRound,
    iconTone: "primary" as const,
    trend: D.prepared,
    trendDirection: "up" as const,
    footer: <span className="text-xs text-muted-foreground">{D.metricCustomersFooter}</span>
  },
  {
    title: D.metricCatalogProducts,
    value: D.metricProductsReady,
    icon: Package,
    iconTone: "purple" as const,
    trend: D.prepared,
    trendDirection: "up" as const,
    footer: <span className="text-xs text-muted-foreground">{D.metricProductsFooter}</span>
  },
  {
    title: D.metricOpenChats,
    value: D.metricChatsReady,
    icon: MessageSquare,
    iconTone: "info" as const,
    trend: D.shell,
    trendDirection: "flat" as const,
    footer: <span className="text-xs text-muted-foreground">{D.metricChatsFooter}</span>
  },
  {
    title: D.metricAutomationRules,
    value: D.metricAutomationsReady,
    icon: Workflow,
    iconTone: "warning" as const,
    trend: D.deferred,
    trendDirection: "flat" as const,
    footer: <span className="text-xs text-muted-foreground">{D.metricAutomationsFooter}</span>
  }
];

const moduleRows: Array<Record<string, ReactNode>> = [
  {
    module: D.rowCustomersModule,
    owner: D.rowCustomersWorkspace,
    status: (
      <span className="inline-flex items-center gap-1.5 text-xs font-medium text-success">
        <CheckCircle2 className="h-3.5 w-3.5" /> {D.prepared}
      </span>
    ),
    next: D.rowCustomersNext
  },
  {
    module: D.rowProductsModule,
    owner: D.rowProductsWorkspace,
    status: (
      <span className="inline-flex items-center gap-1.5 text-xs font-medium text-success">
        <CheckCircle2 className="h-3.5 w-3.5" /> {D.prepared}
      </span>
    ),
    next: D.rowProductsNext
  },
  {
    module: D.rowChatsModule,
    owner: D.rowChatsWorkspace,
    status: (
      <span className="inline-flex items-center gap-1.5 text-xs font-medium text-muted-foreground">
        <Clock className="h-3.5 w-3.5" /> {D.shell}
      </span>
    ),
    next: D.rowChatsNext
  },
  {
    module: D.rowAnalyticsModule,
    owner: D.rowAnalyticsWorkspace,
    status: (
      <span className="inline-flex items-center gap-1.5 text-xs font-medium text-warning">
        <Clock className="h-3.5 w-3.5" /> {D.deferred}
      </span>
    ),
    next: D.rowAnalyticsNext
  },
  {
    module: D.rowAutomationsModule,
    owner: D.rowAutomationsWorkspace,
    status: (
      <span className="inline-flex items-center gap-1.5 text-xs font-medium text-warning">
        <Clock className="h-3.5 w-3.5" /> {D.deferred}
      </span>
    ),
    next: D.rowAutomationsNext
  }
];

export default function DashboardPage() {
  const router = useRouter();
  return (
    <AppShell>
      <DashboardContent>
        <PageHeader
          eyebrow={D.eyebrow}
          title={D.title}
          description={D.description}
          breadcrumbs={[{ label: "Workspace", href: "/dashboard" }, { label: D.title }]}
          status={{ label: "Beta", tone: "info" }}
          actions={
            <>
              <Button variant="outline" size="default" onClick={() => router.push("/dashboard/reports")}>
                <BarChart3 className="h-4 w-4" aria-hidden="true" />
                Ver reportes
              </Button>
              <Button size="default" onClick={() => router.push("/dashboard/customers")}>
                <Plus className="h-4 w-4" aria-hidden="true" />
                {t.customers.workspace.createButton}
              </Button>
            </>
          }
        />

        <section
          aria-label="Métricas clave"
          className="grid gap-4 md:grid-cols-2 xl:grid-cols-4"
        >
          {metrics.map((metric, index) => (
            <MetricCard
              key={metric.title}
              {...metric}
              delay={index * 0.05}
            />
          ))}
        </section>

        <Card>
          <CardContent>
            <SectionHeader
              title={D.moduleReadiness}
              description={D.moduleReadinessDesc}
              action={
                <Button variant="outline" size="sm">
                  {D.viewRoadmap}
                </Button>
              }
              className="mb-4"
            />
            <DataTable
              columns={[
                { key: "module", header: D.tableHeaderModule, sortable: true },
                { key: "owner", header: D.tableHeaderWorkspace },
                { key: "status", header: D.tableHeaderStatus },
                { key: "next", header: D.tableHeaderNext }
              ]}
              rows={moduleRows}
              emptyTitle={D.noModulesTitle}
              emptyDescription={D.noModulesDesc}
            />
          </CardContent>
        </Card>

        <div className="grid gap-4 xl:grid-cols-[1.1fr_0.9fr]">
          <Card variant="elevated">
            <CardContent>
              <SectionHeader
                title={D.loadingSection}
                description={D.loadingDesc}
                className="mb-4"
              />
              <ActivityHeatmap />
            </CardContent>
          </Card>

          <Card variant="glow">
            <CardContent>
              <SectionHeader
                title={D.nextPhase}
                description={D.nextPhaseDesc}
                className="mb-4"
              />
              <EmptyState
                  icon={Sparkles}
                  title={D.emptyTitle}
                  description={D.emptyDesc}
                  variant="minimal"
                />
            </CardContent>
          </Card>
        </div>
      </DashboardContent>
    </AppShell>
  );
}

function ActivityHeatmap() {
  const days = ["L", "M", "X", "J", "V", "S", "D"];
  const weeks = 12;
  const heatLevels = 4;
  const cells = Array.from({ length: 7 * weeks }, (_, i) => {
    return (Math.sin(i * 0.7) + 1) * 1.5;
  });
  return (
    <div>
      <div className="mb-3 flex items-center justify-between text-xs text-muted-foreground">
        <span>Últimas {weeks} semanas</span>
        <div className="flex items-center gap-1.5">
          <span className="text-[10px]">Menos</span>
          {Array.from({ length: heatLevels }).map((_, i) => (
            <span
              key={i}
              className={cn(
                "h-3 w-3 rounded-sm",
                i === 0 && "bg-primary-100",
                i === 1 && "bg-primary-200",
                i === 2 && "bg-primary-300",
                i === 3 && "bg-primary"
              )}
            />
          ))}
          <span className="text-[10px]">Más</span>
        </div>
      </div>
      <div className="grid grid-cols-[20px_repeat(12,minmax(0,1fr))] gap-1.5">
        {days.map((d, dayIdx) => (
          <DayRow
            key={d}
            day={d}
            dayIdx={dayIdx}
            weeks={weeks}
            cells={cells}
          />
        ))}
      </div>
      <div className="mt-4 flex items-center gap-3 text-xs text-muted-foreground">
        <StatDelta value="+24%" direction="up" size="sm" />
        <span>vs. trimestre anterior</span>
      </div>
    </div>
  );
}

function DayRow({
  day,
  dayIdx,
  weeks,
  cells
}: {
  day: string;
  dayIdx: number;
  weeks: number;
  cells: number[];
}) {
  return (
    <>
      <span className="flex items-center text-[10px] font-medium text-muted-foreground">
        {day}
      </span>
      {Array.from({ length: weeks }).map((_, wIdx) => {
        const v = cells[dayIdx * weeks + wIdx] % 4;
        return (
          <span
            key={`${dayIdx}-${wIdx}`}
            className={cn(
              "h-4 w-full rounded-sm transition-colors hover:ring-1 hover:ring-primary-300",
              v < 1 && "bg-primary-100",
              v >= 1 && v < 2 && "bg-primary-200",
              v >= 2 && v < 3 && "bg-primary-300",
              v >= 3 && "bg-primary"
            )}
            title={`Semana ${wIdx + 1} - ${day}`}
          />
        );
      })}
    </>
  );
}
