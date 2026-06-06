"use client";

import { t } from "@/lib/i18n";
import { Customer360Workspace } from "@/modules/crm/components/customer-360-workspace";
import { AppShell } from "@/components/layout/app-shell";
import { DashboardContent } from "@/components/layout/dashboard-content";
import { DashboardHeader } from "@/components/layout/dashboard-header";
import { ExportReportButtons } from "@/modules/reporting";

const C = t.crm.page;

export default function CustomersPage() {
  return (
    <AppShell>
      <DashboardContent>
        <DashboardHeader
          eyebrow={C.eyebrow}
          title={C.title}
          description={C.description}
          action={<ExportReportButtons report="crm" />}
        />
        <Customer360Workspace />
      </DashboardContent>
    </AppShell>
  );
}
