"use client";

import { AppShell } from "@/components/layout/app-shell";
import { DashboardContent } from "@/components/layout/dashboard-content";
import { PageHeader } from "@/components/layout/page-header";
import { OrdersWorkspace } from "@/modules/orders";
import { ExportReportButtons } from "@/modules/reporting";

export default function OrdersPage() {
  return (
    <AppShell>
      <DashboardContent>
        <PageHeader
          eyebrow="Operaciones"
          title="Pedidos"
          description="Gestiona pedidos confirmados por la IA, estados de preparación, entrega y ventas por periodo."
          breadcrumbs={[
            { label: "Workspace", href: "/dashboard" },
            { label: "Pedidos" }
          ]}
          status={{ label: "En vivo", tone: "success" }}
          actions={<ExportReportButtons report="sales" />}
        />
        <OrdersWorkspace />
      </DashboardContent>
    </AppShell>
  );
}
