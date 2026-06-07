"use client";

import { AppShell } from "@/components/layout/app-shell";
import { DashboardContent } from "@/components/layout/dashboard-content";
import { DashboardHeader } from "@/components/layout/dashboard-header";
import { AutomationWorkspace } from "@/modules/automation/workspace";

export default function TasksPage() {
  return (
    <AppShell>
      <DashboardContent>
        <DashboardHeader
          eyebrow="Automatización"
          title="Task Center comercial"
          description="Tareas, alertas, seguimientos y cierres generados automáticamente por el motor de automatización."
        />
        <AutomationWorkspace />
      </DashboardContent>
    </AppShell>
  );
}
