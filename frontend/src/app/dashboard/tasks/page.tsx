"use client";

import { AppShell } from "@/components/layout/app-shell";
import { DashboardContent } from "@/components/layout/dashboard-content";
import { PageHeader } from "@/components/layout/page-header";
import { AutomationWorkspace } from "@/modules/automation/workspace";

export default function TasksPage() {
  return (
    <AppShell>
      <DashboardContent>
        <PageHeader
          eyebrow="Automatización"
          title="Task Center comercial"
          description="Tareas, alertas, seguimientos y cierres generados automáticamente por el motor de automatización."
          breadcrumbs={[
            { label: "Workspace", href: "/dashboard" },
            { label: "Automatización" },
            { label: "Task Center" }
          ]}
        />
        <AutomationWorkspace />
      </DashboardContent>
    </AppShell>
  );
}
