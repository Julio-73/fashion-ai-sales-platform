"use client";

import { AppShell } from "@/components/layout/app-shell";
import { DashboardContent } from "@/components/layout/dashboard-content";
import { DashboardHeader } from "@/components/layout/dashboard-header";
import { AutomationsWorkspace } from "@/modules/automations";

export default function AutomationsPage() {
  return (
    <AppShell>
      <DashboardContent>
        <DashboardHeader
          eyebrow="Automatización"
          title="Automatizaciones"
          description="Diseña reglas que responden, etiquetan, priorizan y dan seguimiento a clientes sin perder control comercial."
        />
        <AutomationsWorkspace />
      </DashboardContent>
    </AppShell>
  );
}
