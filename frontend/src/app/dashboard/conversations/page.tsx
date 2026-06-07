"use client";

import { t } from "@/lib/i18n";
import { ConversationsWorkspace } from "@/modules/conversations/components/conversations-workspace";
import { AppShell } from "@/components/layout/app-shell";
import { DashboardContent } from "@/components/layout/dashboard-content";
import { PageHeader } from "@/components/layout/page-header";

const C = t.conversations.page;

export default function ConversationsPage() {
  return (
    <AppShell>
      <DashboardContent>
        <PageHeader
          eyebrow={C.eyebrow}
          title={C.title}
          description={C.description}
          breadcrumbs={[
            { label: "Workspace", href: "/dashboard" },
            { label: "Conversaciones" }
          ]}
        />
        <ConversationsWorkspace />
      </DashboardContent>
    </AppShell>
  );
}
