"use client";

import { MessageSquare, Package, UsersRound, BarChart3 } from "lucide-react";

import { t } from "@/lib/i18n";
import { AppShell } from "@/components/layout/app-shell";
import { DashboardHeader } from "@/components/layout/dashboard-header";
import { MetricCard } from "@/components/ui/metric-card";
import { EmptyState } from "@/components/feedback/empty-state";
import { StatusBadge } from "@/components/ui/status-badge";

const D = t.dashboard.home;

const modules = [
  { name: D.rowCustomersModule, status: D.prepared, icon: UsersRound },
  { name: D.rowProductsModule, status: D.shell, icon: Package },
  { name: D.rowChatsModule, status: D.shell, icon: MessageSquare },
  { name: D.rowAnalyticsModule, status: D.prepared, icon: BarChart3 }
];

export default function HomePage() {
  return (
    <AppShell>
      <DashboardHeader
        eyebrow={D.eyebrow}
        title={D.title}
        description={D.description}
      />

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {modules.map((module) => (
          <MetricCard
            key={module.name}
            title={module.name}
            value={module.status}
            icon={module.icon}
            footer={<StatusBadge tone="success">{D.prepared}</StatusBadge>}
          />
        ))}
      </section>

      <section className="mt-6">
        <EmptyState
          title={D.emptyTitle}
          description={D.emptyDesc}
        />
      </section>
    </AppShell>
  );
}
