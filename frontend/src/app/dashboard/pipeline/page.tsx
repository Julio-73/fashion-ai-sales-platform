"use client";

import { PipelineWorkspace } from "@/components/pipeline/pipeline-workspace";
import { AppShell } from "@/components/layout/app-shell";
import { DashboardContent } from "@/components/layout/dashboard-content";
import { DashboardHeader } from "@/components/layout/dashboard-header";

export default function PipelinePage() {
  return (
    <AppShell>
      <DashboardContent>
        <DashboardHeader
          eyebrow="Ventas"
          title="Pipeline comercial"
          description="Embudo kanban con IA comercial, automatizaciones y reportes en vivo."
        />
        <PipelineWorkspace />
      </DashboardContent>
    </AppShell>
  );
}
