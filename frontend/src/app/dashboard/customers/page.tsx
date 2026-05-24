"use client";

import { Plus } from "lucide-react";

import { t } from "@/lib/i18n";
import { CustomersCrmWorkspace } from "@/modules/customers/components/customers-crm-workspace";
import { AppShell } from "@/components/layout/app-shell";
import { DashboardContent } from "@/components/layout/dashboard-content";
import { DashboardHeader } from "@/components/layout/dashboard-header";
import { Button } from "@/components/ui/button";

const C = t.customers.page;

export default function CustomersPage() {
  return (
    <AppShell>
      <DashboardContent>
        <DashboardHeader
          eyebrow={C.eyebrow}
          title={C.title}
          description={C.description}
          action={
            <Button type="button">
              <Plus className="h-4 w-4" aria-hidden="true" />
              {C.importButton}
            </Button>
          }
        />
        <CustomersCrmWorkspace />
      </DashboardContent>
    </AppShell>
  );
}

