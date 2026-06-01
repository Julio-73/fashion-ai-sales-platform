"use client";

import { AppShell } from "@/components/layout/app-shell";
import { DashboardContent } from "@/components/layout/dashboard-content";
import { DashboardHeader } from "@/components/layout/dashboard-header";
import { OrdersWorkspace } from "@/modules/orders";

export default function OrdersPage() {
  return (
    <AppShell>
      <DashboardContent>
        <DashboardHeader
          eyebrow="Operaciones"
          title="Pedidos"
          description="Gestiona pedidos confirmados por la IA, estados de preparación, entrega y ventas por periodo."
        />
        <OrdersWorkspace />
      </DashboardContent>
    </AppShell>
  );
}
