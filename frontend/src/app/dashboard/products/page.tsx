"use client";

import { t } from "@/lib/i18n";
import { ProductCatalogWorkspace } from "@/modules/products/components/product-catalog-workspace";
import { AppShell } from "@/components/layout/app-shell";
import { DashboardContent } from "@/components/layout/dashboard-content";
import { DashboardHeader } from "@/components/layout/dashboard-header";

const P = t.products.page;

export default function ProductsPage() {
  return (
    <AppShell>
      <DashboardContent>
        <DashboardHeader
          eyebrow={P.eyebrow}
          title={P.title}
          description={P.description}
        />
        <ProductCatalogWorkspace />
      </DashboardContent>
    </AppShell>
  );
}
