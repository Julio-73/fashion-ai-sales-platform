"use client";

import { AppShell } from "@/components/layout/app-shell";
import { DashboardContent } from "@/components/layout/dashboard-content";
import { DashboardHeader } from "@/components/layout/dashboard-header";
import { t } from "@/lib/i18n";
import { ReportsWorkspace } from "@/modules/reporting";

const R = t.reporting;

export default function ReportsPage() {
  return (
    <AppShell>
      <DashboardContent>
        <DashboardHeader
          eyebrow={R.eyebrow}
          title={R.title}
          description={R.description}
        />
        <ReportsWorkspace />
      </DashboardContent>
    </AppShell>
  );
}
