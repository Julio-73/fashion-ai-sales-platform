"use client";

import { AppShell } from "@/components/layout/app-shell";
import { DashboardContent } from "@/components/layout/dashboard-content";
import { DashboardHeader } from "@/components/layout/dashboard-header";
import { InventoryWorkspace } from "@/modules/inventory";

export default function InventoryPage() {
  return (
    <AppShell>
      <DashboardContent>
        <DashboardHeader
          eyebrow="Operaciones"
          title="Inventario"
          description="Controla existencias, movimientos, reservas y alertas de stock por empresa."
        />
        <InventoryWorkspace />
      </DashboardContent>
    </AppShell>
  );
}
