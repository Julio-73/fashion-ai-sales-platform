"use client";

import { AppShell } from "@/components/layout/app-shell";
import { DashboardContent } from "@/components/layout/dashboard-content";
import { PageHeader } from "@/components/layout/page-header";
import { ExportReportButtons } from "@/modules/reporting";
import { ExecutiveDashboardWorkspace } from "@/modules/executive-dashboard";

export default function ExecutiveDashboardPage() {
  return (
    <AppShell>
      <DashboardContent>
        <PageHeader
          eyebrow="Ejecutivo"
          title="Dashboard Ejecutivo"
          description="Visión 360° del negocio en una sola pantalla: ventas, clientes, pipeline, IA comercial y alertas críticas."
          breadcrumbs={[
            { label: "Workspace", href: "/dashboard" },
            { label: "Dashboard Ejecutivo" }
          ]}
          status={{ label: "En vivo", tone: "success" }}
          actions={<ExportReportButtons report="executive" />}
        />
        <ExecutiveDashboardWorkspace />
      </DashboardContent>
    </AppShell>
  );
}
