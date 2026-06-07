"use client";

import { PipelineWorkspace } from "@/components/pipeline/pipeline-workspace";
import { AppShell } from "@/components/layout/app-shell";
import { DashboardContent } from "@/components/layout/dashboard-content";
import { PageHeader } from "@/components/layout/page-header";
import { ExportReportButtons } from "@/modules/reporting";

export default function PipelinePage() {
  return (
    <AppShell>
      <DashboardContent>
        <PageHeader
          eyebrow="Ventas"
          title="Pipeline comercial"
          description="Embudo kanban con IA comercial, automatizaciones y reportes en vivo."
          breadcrumbs={[
            { label: "Workspace", href: "/dashboard" },
            { label: "Pipeline" }
          ]}
          status={{ label: "Tiempo real", tone: "success" }}
          actions={<ExportReportButtons report="pipeline" />}
        />
        <PipelineWorkspace />
      </DashboardContent>
    </AppShell>
  );
}
