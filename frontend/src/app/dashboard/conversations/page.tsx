"use client";

import { t } from "@/lib/i18n";
import { ConversationsWorkspace } from "@/modules/conversations/components/conversations-workspace";
import { AppShell } from "@/components/layout/app-shell";
import { DashboardContent } from "@/components/layout/dashboard-content";
import { DashboardHeader } from "@/components/layout/dashboard-header";

const C = t.conversations.page;

export default function ConversationsPage() {
  return (
    <AppShell>
      <DashboardContent>
        <DashboardHeader
          eyebrow={C.eyebrow}
          title={C.title}
          description={C.description}
        />
        <ConversationsWorkspace />
      </DashboardContent>
    </AppShell>
  );
}
