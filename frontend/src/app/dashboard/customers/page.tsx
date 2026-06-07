"use client";

import { t } from "@/lib/i18n";
import { Customer360Workspace } from "@/modules/crm/components/customer-360-workspace";
import { AppShell } from "@/components/layout/app-shell";
import { DashboardContent } from "@/components/layout/dashboard-content";
import { PageHeader } from "@/components/layout/page-header";
import { ExportReportButtons } from "@/modules/reporting";

const C = t.crm.page;

export default function CustomersPage() {
  return (
    <AppShell>
      <DashboardContent>
        <PageHeader
          eyebrow={C.eyebrow}
          title={C.title}
          description={C.description}
          breadcrumbs={[
            { label: "Workspace", href: "/dashboard" },
            { label: "CRM" },
            { label: C.title }
          ]}
          actions={<ExportReportButtons report="crm" />}
        />
        <Customer360Workspace />
      </DashboardContent>
    </AppShell>
  );
}
