"use client";

import { AppShell } from "@/components/layout/app-shell";
import { DashboardContent } from "@/components/layout/dashboard-content";
import { DashboardHeader } from "@/components/layout/dashboard-header";
import { WhatsappWorkspace } from "@/modules/whatsapp";

export default function WhatsappPage() {
  return (
    <AppShell>
      <DashboardContent>
        <DashboardHeader
          eyebrow="Canales"
          title="WhatsApp Business"
          description="Conecta tu número de WhatsApp Business Cloud API. Los mensajes reales se enrutan al Smart Sales Brain y actualizan el CRM."
        />
        <WhatsappWorkspace />
      </DashboardContent>
    </AppShell>
  );
}
