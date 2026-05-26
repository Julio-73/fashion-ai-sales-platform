"use client";

import { t } from "@/lib/i18n";
import { AiSalesDashboard } from "@/components/ai-sales/ai-sales-dashboard";
import { AppShell } from "@/components/layout/app-shell";
import { DashboardContent } from "@/components/layout/dashboard-content";
import { DashboardHeader } from "@/components/layout/dashboard-header";

const S = t.sales.page;

export default function AiSalesPage() {
  return (
    <AppShell>
      <DashboardContent>
        <DashboardHeader
          eyebrow={S.eyebrow}
          title={S.title}
          description={S.description}
        />
        <AiSalesDashboard />
      </DashboardContent>
    </AppShell>
  );
}
