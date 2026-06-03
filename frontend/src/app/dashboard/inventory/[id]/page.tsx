"use client";

import { AppShell } from "@/components/layout/app-shell";
import { DashboardContent } from "@/components/layout/dashboard-content";
import { DashboardHeader } from "@/components/layout/dashboard-header";
import { InventoryDetail } from "@/modules/inventory";

type PageProps = {
  params: { id: string };
};

export default function InventoryProductPage({ params }: PageProps) {
  const { id } = params;
  return (
    <AppShell>
      <DashboardContent>
        <DashboardHeader
          eyebrow="Operaciones"
          title="Detalle de inventario"
          description="Stock, movimientos, reservas activas y resumen global del producto."
        />
        <InventoryDetail productId={id} />
      </DashboardContent>
    </AppShell>
  );
}
