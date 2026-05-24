"use client";

import { BarChart3, MessageSquare, Package, Plus, Sparkles, UsersRound, Workflow } from "lucide-react";
import type { ReactNode } from "react";

import { t } from "@/lib/i18n";
import { DataTable } from "@/components/data-table/data-table";
import { EmptyState } from "@/components/feedback/empty-state";
import { AppShell } from "@/components/layout/app-shell";
import { DashboardContent } from "@/components/layout/dashboard-content";
import { DashboardHeader } from "@/components/layout/dashboard-header";
import { DashboardSection } from "@/components/layout/dashboard-section";
import { Button } from "@/components/ui/button";
import { MetricCard } from "@/components/ui/metric-card";
import { DashboardSkeleton } from "@/components/ui/skeleton";
import { StatusBadge } from "@/components/ui/status-badge";

const D = t.dashboard.home;

const metrics = [
  {
    title: D.metricActiveCustomers,
    value: D.metricCustomersReady,
    trend: D.prepared,
    icon: UsersRound,
    footer: <span className="text-xs text-muted-foreground">{D.metricCustomersFooter}</span>
  },
  {
    title: D.metricCatalogProducts,
    value: D.metricProductsReady,
    trend: D.prepared,
    icon: Package,
    footer: <span className="text-xs text-muted-foreground">{D.metricProductsFooter}</span>
  },
  {
    title: D.metricOpenChats,
    value: D.metricChatsReady,
    trend: D.shell,
    icon: MessageSquare,
    footer: <span className="text-xs text-muted-foreground">{D.metricChatsFooter}</span>
  },
  {
    title: D.metricAutomationRules,
    value: D.metricAutomationsReady,
    trend: D.deferred,
    icon: Workflow,
    footer: <span className="text-xs text-muted-foreground">{D.metricAutomationsFooter}</span>
  }
];

const moduleRows: Array<Record<string, ReactNode>> = [
  {
    module: D.rowCustomersModule,
    owner: D.rowCustomersWorkspace,
    status: <StatusBadge tone="success">{D.prepared}</StatusBadge>,
    next: D.rowCustomersNext
  },
  {
    module: D.rowProductsModule,
    owner: D.rowProductsWorkspace,
    status: <StatusBadge tone="success">{D.prepared}</StatusBadge>,
    next: D.rowProductsNext
  },
  {
    module: D.rowChatsModule,
    owner: D.rowChatsWorkspace,
    status: <StatusBadge tone="neutral">{D.shell}</StatusBadge>,
    next: D.rowChatsNext
  },
  {
    module: D.rowAnalyticsModule,
    owner: D.rowAnalyticsWorkspace,
    status: <StatusBadge tone="warning">{D.deferred}</StatusBadge>,
    next: D.rowAnalyticsNext
  },
  {
    module: D.rowAutomationsModule,
    owner: D.rowAutomationsWorkspace,
    status: <StatusBadge tone="warning">{D.deferred}</StatusBadge>,
    next: D.rowAutomationsNext
  }
];

export default function DashboardPage() {
  return (
    <AppShell>
      <DashboardContent>
        <DashboardHeader
          eyebrow={D.eyebrow}
          title={D.title}
          description={D.description}
          action={
            <Button type="button">
              <Plus className="h-4 w-4" aria-hidden="true" />
              {t.customers.workspace.createButton}
            </Button>
          }
        />

        <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {metrics.map((metric, index) => (
            <MetricCard key={metric.title} {...metric} delay={index * 0.04} />
          ))}
        </section>

        <DashboardSection
          title={D.moduleReadiness}
          description={D.moduleReadinessDesc}
          action={
            <Button type="button" variant="outline">
              {D.viewRoadmap}
            </Button>
          }
        >
          <DataTable
            columns={[
              { key: "module", header: D.tableHeaderModule },
              { key: "owner", header: D.tableHeaderWorkspace },
              { key: "status", header: D.tableHeaderStatus },
              { key: "next", header: D.tableHeaderNext }
            ]}
            rows={moduleRows}
            emptyTitle={D.noModulesTitle}
            emptyDescription={D.noModulesDesc}
          />
        </DashboardSection>

        <div className="grid gap-4 xl:grid-cols-[1.1fr_0.9fr]">
          <DashboardSection
            title={D.loadingSection}
            description={D.loadingDesc}
          >
            <DashboardSkeleton />
          </DashboardSection>

          <DashboardSection
            title={D.nextPhase}
            description={D.nextPhaseDesc}
          >
            <EmptyState
              icon={Sparkles}
              title={D.emptyTitle}
              description={D.emptyDesc}
            />
          </DashboardSection>
        </div>
      </DashboardContent>
    </AppShell>
  );
}
