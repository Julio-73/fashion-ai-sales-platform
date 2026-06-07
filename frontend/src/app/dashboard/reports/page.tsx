"use client";

import { AppShell } from "@/components/layout/app-shell";
import { DashboardContent } from "@/components/layout/dashboard-content";
import { PageHeader } from "@/components/layout/page-header";
import { t } from "@/lib/i18n";
import { ReportsWorkspace } from "@/modules/reporting";

const R = t.reporting;

export default function ReportsPage() {
  return (
    <AppShell>
      <DashboardContent>
        <PageHeader
          eyebrow={R.eyebrow}
          title={R.title}
          description={R.description}
          breadcrumbs={[
            { label: "Workspace", href: "/dashboard" },
            { label: "Reportes" }
          ]}
        />
        <ReportsWorkspace />
      </DashboardContent>
    </AppShell>
  );
}
