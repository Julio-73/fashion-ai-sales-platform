"use client";

import { AppShell } from "@/components/layout/app-shell";
import { DashboardContent } from "@/components/layout/dashboard-content";
import { DashboardHeader } from "@/components/layout/dashboard-header";
import { ExecutiveDashboardWorkspace } from "@/modules/executive-dashboard";

export default function ExecutiveDashboardPage() {
  return (
    <AppShell>
      <DashboardContent>
        <DashboardHeader
          eyebrow="Ejecutivo"
          title="Dashboard Ejecutivo"
          description="Visión 360° del negocio en una sola pantalla: ventas, clientes, pipeline, IA comercial y alertas críticas."
        />
        <ExecutiveDashboardWorkspace />
      </DashboardContent>
    </AppShell>
  );
}
