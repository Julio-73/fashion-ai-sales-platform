"use client";

import { AppShell } from "@/components/layout/app-shell";
import { DashboardContent } from "@/components/layout/dashboard-content";
import { PageHeader } from "@/components/layout/page-header";
import { AutomationsWorkspace } from "@/modules/automations";

export default function AutomationsPage() {
  return (
    <AppShell>
      <DashboardContent>
        <PageHeader
          eyebrow="Automatización"
          title="Automatizaciones"
          description="Diseña reglas que responden, etiquetan, priorizan y dan seguimiento a clientes sin perder control comercial."
          breadcrumbs={[
            { label: "Workspace", href: "/dashboard" },
            { label: "Automatización" },
            { label: "Automatizaciones" }
          ]}
          status={{ label: "12 reglas activas", tone: "success" }}
        />
        <AutomationsWorkspace />
      </DashboardContent>
    </AppShell>
  );
}
