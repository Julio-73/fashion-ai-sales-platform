"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  AlertCircle,
  AlertTriangle,
  CheckCircle2,
  MessageCircle,
  Phone,
  Send,
  Webhook,
} from "lucide-react";

import { DataTable } from "@/components/data-table/data-table";
import { DashboardSection } from "@/components/layout/dashboard-section";
import { Button } from "@/components/ui/button";
import { MetricCard } from "@/components/ui/metric-card";
import { Skeleton } from "@/components/ui/skeleton";
import { StatusBadge } from "@/components/ui/status-badge";
import { ApiError } from "@/services/api-client";
import { useAuthStore } from "@/store/auth-store";
import {
  getWhatsappMetrics,
  listWhatsappAccounts,
  listWhatsappMessages,
  listWhatsappWebhooks,
  sendWhatsappMessage,
} from "@/modules/whatsapp/services/whatsapp-api";
import type {
  WhatsappAccount,
  WhatsappMessage,
  WhatsappMetrics,
  WhatsappWebhook,
} from "@/types/whatsapp";

type Tone = "success" | "warning" | "neutral";

const statusTone: Record<string, Tone> = {
  sent: "success",
  delivered: "success",
  read: "success",
  failed: "warning",
  pending: "warning",
};

const eventTone: Record<string, Tone> = {
  message: "success",
  status: "neutral",
  verification: "warning",
  unknown: "neutral",
};

const statusLabel: Record<string, string> = {
  sent: "Enviado",
  delivered: "Entregado",
  read: "Leído",
  failed: "Fallido",
  pending: "Pendiente",
};

const eventLabel: Record<string, string> = {
  message: "Mensaje",
  status: "Estado",
  verification: "Verificación",
  unknown: "Desconocido",
};

const directionLabel: Record<string, string> = {
  inbound: "Entrante",
  outbound: "Saliente",
};

function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleString("es-PE", {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function truncateBody(body: string | null, max: number = 80): string {
  if (!body) return "—";
  if (body.length <= max) return body;
  return body.slice(0, max - 1) + "…";
}

type MessageRow = {
  id: string;
  direction: React.ReactNode;
  from_to: React.ReactNode;
  body: React.ReactNode;
  status: React.ReactNode;
  created: string;
};

type WebhookRow = {
  id: string;
  event: React.ReactNode;
  phone: React.ReactNode;
  processed: React.ReactNode;
  error: React.ReactNode;
  received: string;
};

export function WhatsappWorkspace() {
  const { accessToken, refreshSession } = useAuthStore();
  const [metrics, setMetrics] = useState<WhatsappMetrics | null>(null);
  const [accounts, setAccounts] = useState<WhatsappAccount[]>([]);
  const [messages, setMessages] = useState<WhatsappMessage[]>([]);
  const [webhooks, setWebhooks] = useState<WhatsappWebhook[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sendTo, setSendTo] = useState("");
  const [sendBody, setSendBody] = useState("");
  const [sendSending, setSendSending] = useState(false);
  const [sendFeedback, setSendFeedback] = useState<string | null>(null);
  const activeRef = useRef(true);

  const load = useCallback(
    async (retried = false) => {
      if (!accessToken) return;
      setIsLoading(true);
      setError(null);
      try {
        const [m, a, msgs, w] = await Promise.all([
          getWhatsappMetrics(accessToken),
          listWhatsappAccounts(accessToken),
          listWhatsappMessages(accessToken, { limit: 15 }),
          listWhatsappWebhooks(accessToken, { limit: 10 }),
        ]);
        if (!activeRef.current) return;
        setMetrics(m);
        setAccounts(a);
        setMessages(msgs.items);
        setWebhooks(w.items);
      } catch (err) {
        if (!activeRef.current) return;
        if (!retried && err instanceof ApiError && err.status === 401) {
          try {
            await refreshSession();
          } catch {
            setError("No se pudo cargar WhatsApp. La sesión no es válida.");
            setIsLoading(false);
            return;
          }
          return load(true);
        }
        setError(
          "No se pudo cargar la información de WhatsApp. Verifica el backend y los permisos.",
        );
      } finally {
        if (activeRef.current) setIsLoading(false);
      }
    },
    [accessToken, refreshSession],
  );

  useEffect(() => {
    activeRef.current = true;
    load();
    return () => {
      activeRef.current = false;
    };
  }, [load]);

  const handleSend = useCallback(async () => {
    if (!accessToken) return;
    if (!sendTo.trim() || !sendBody.trim()) {
      setSendFeedback("Completa el teléfono y el mensaje.");
      return;
    }
    setSendSending(true);
    setSendFeedback(null);
    try {
      const digits = sendTo.replace(/[^0-9+]/g, "").replace(/^\+/, "");
      const result = await sendWhatsappMessage(accessToken, {
        to_phone: digits,
        body: sendBody,
      });
      if (result.accepted) {
        setSendFeedback("Mensaje enviado correctamente.");
        setSendTo("");
        setSendBody("");
        load();
      } else {
        setSendFeedback("El proveedor rechazó el mensaje. Revisa credenciales.");
      }
    } catch (err) {
      if (err instanceof ApiError) {
        setSendFeedback(`Error: ${err.message}`);
      } else {
        setSendFeedback("Error de red al enviar el mensaje.");
      }
    } finally {
      setSendSending(false);
    }
  }, [accessToken, sendTo, sendBody, load]);

  const activeAccount = accounts.find((a) => a.is_active) ?? accounts[0] ?? null;

  const messageRows: MessageRow[] = messages.map((m) => ({
    id: m.id,
    direction: (
      <StatusBadge tone={m.direction === "inbound" ? "warning" : "success"}>
        {directionLabel[m.direction] ?? m.direction}
      </StatusBadge>
    ),
    from_to: (
      <span className="text-xs text-muted-foreground">
        {m.from_phone} → {m.to_phone}
      </span>
    ),
    body: <span className="text-sm">{truncateBody(m.body)}</span>,
    status: (
      <StatusBadge tone={statusTone[m.status] ?? "neutral"}>
        {statusLabel[m.status] ?? m.status}
      </StatusBadge>
    ),
    created: formatDateTime(m.created_at),
  }));

  const webhookRows: WebhookRow[] = webhooks.map((w) => ({
    id: w.id,
    event: (
      <StatusBadge tone={eventTone[w.event_type] ?? "neutral"}>
        {eventLabel[w.event_type] ?? w.event_type}
      </StatusBadge>
    ),
    phone: <span className="font-mono text-xs">{w.phone_number_id ?? "—"}</span>,
    processed: (
      <StatusBadge tone={w.processed && !w.error ? "success" : "warning"}>
        {w.processed && !w.error ? "OK" : w.error ? "Error" : "Pendiente"}
      </StatusBadge>
    ),
    error: w.error ? (
      <span className="text-xs text-destructive">{truncateBody(w.error, 60)}</span>
    ) : (
      <span className="text-xs text-muted-foreground">—</span>
    ),
    received: formatDateTime(w.received_at),
  }));

  return (
    <div className="grid gap-6">
      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          title="Conexión"
          value={metrics?.is_configured ? "Activa" : "Sin configurar"}
          icon={metrics?.is_configured ? CheckCircle2 : AlertCircle}
          footer={
            <span className="text-xs text-muted-foreground">
              {metrics?.active_accounts ?? 0} cuenta
              {metrics?.active_accounts === 1 ? "" : "s"} activa
              {metrics?.active_accounts === 1 ? "" : "s"}
            </span>
          }
        />
        <MetricCard
          title="Recibidos (24h)"
          value={String(metrics?.inbound_last_24h ?? 0)}
          icon={MessageCircle}
          footer={
            <span className="text-xs text-muted-foreground">
              {metrics?.inbound_total ?? 0} mensajes en total
            </span>
          }
          delay={0.04}
        />
        <MetricCard
          title="Enviados (24h)"
          value={String(metrics?.outbound_last_24h ?? 0)}
          icon={Send}
          footer={
            <span className="text-xs text-muted-foreground">
              {metrics?.delivered_total ?? 0} entregados ·{" "}
              {metrics?.failed_total ?? 0} fallidos
            </span>
          }
          delay={0.08}
        />
        <MetricCard
          title="Webhooks (24h)"
          value={String(metrics?.webhooks_last_24h ?? 0)}
          icon={Webhook}
          footer={
            <span className="text-xs text-muted-foreground">
              {metrics?.webhooks_failed_last_24h ?? 0} con error
            </span>
          }
          delay={0.12}
        />
      </section>

      {metrics && !metrics.is_configured ? (
        <section className="rounded-lg border border-amber-300 bg-amber-50 px-4 py-3 text-sm text-amber-900">
          <div className="flex items-center gap-2 font-medium">
            <AlertTriangle className="h-4 w-4" />
            WhatsApp no está configurado
          </div>
          <p className="mt-1 text-xs opacity-80">
            Crea una cuenta con tus credenciales de Meta para empezar a recibir y enviar
            mensajes.
          </p>
        </section>
      ) : null}

      {error ? (
        <section className="rounded-lg border border-destructive/25 bg-destructive/10 px-4 py-3 text-sm text-destructive">
          {error}
        </section>
      ) : null}

      <DashboardSection
        title="Cuenta conectada"
        description="Estado y credenciales de la integración con Meta Cloud API"
      >
        {isLoading ? (
          <Skeleton className="h-24 w-full" />
        ) : !activeAccount ? (
          <div className="grid gap-2 rounded-md border bg-background p-4 text-sm text-muted-foreground">
            <p>Aún no se ha registrado ninguna cuenta de WhatsApp.</p>
            <p className="text-xs">
              Configura una con{" "}
              <code className="rounded bg-secondary px-1.5 py-0.5">
                POST /api/v1/whatsapp/accounts
              </code>{" "}
              o desde el panel de Meta.
            </p>
          </div>
        ) : (
          <div className="grid gap-3 rounded-md border bg-background p-4 md:grid-cols-3">
            <div className="flex items-start gap-3">
              <Phone className="mt-0.5 h-4 w-4 text-muted-foreground" />
              <div>
                <p className="text-xs text-muted-foreground">Número</p>
                <p className="font-medium">
                  {activeAccount.display_phone_number ?? activeAccount.phone_number_id}
                </p>
                <p className="text-xs text-muted-foreground">
                  ID: {activeAccount.phone_number_id}
                </p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <Webhook className="mt-0.5 h-4 w-4 text-muted-foreground" />
              <div>
                <p className="text-xs text-muted-foreground">API</p>
                <p className="font-medium">{activeAccount.api_version}</p>
                <p className="text-xs text-muted-foreground">
                  Negocio: {activeAccount.business_account_id ?? "—"}
                </p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <CheckCircle2 className="mt-0.5 h-4 w-4 text-muted-foreground" />
              <div>
                <p className="text-xs text-muted-foreground">Estado</p>
                <StatusBadge tone={activeAccount.is_active ? "success" : "neutral"}>
                  {activeAccount.is_active ? "Activo" : "Inactivo"}
                </StatusBadge>
                <p className="mt-1 text-xs text-muted-foreground">
                  Conectado el {formatDateTime(activeAccount.created_at)}
                </p>
              </div>
            </div>
          </div>
        )}
      </DashboardSection>

      <DashboardSection
        title="Enviar mensaje"
        description="Push manual a un número de WhatsApp. Usa el modo dry-run si aún no hay token real."
      >
        <div className="grid gap-3 rounded-md border bg-background p-4 md:grid-cols-[minmax(0,1fr)_minmax(0,2fr)_auto]">
          <div>
            <label className="mb-1 block text-xs font-medium text-muted-foreground">
              Teléfono (con prefijo país)
            </label>
            <input
              className="h-10 w-full rounded-md border bg-background px-3 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
              placeholder="+51999999999"
              value={sendTo}
              onChange={(e) => setSendTo(e.target.value)}
            />
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-muted-foreground">
              Mensaje
            </label>
            <input
              className="h-10 w-full rounded-md border bg-background px-3 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
              placeholder="Hola, te escribimos desde la plataforma…"
              value={sendBody}
              onChange={(e) => setSendBody(e.target.value)}
            />
          </div>
          <div className="flex items-end">
            <Button
              type="button"
              onClick={handleSend}
              disabled={sendSending || !metrics?.is_configured}
            >
              <Send className="mr-2 h-4 w-4" />
              {sendSending ? "Enviando…" : "Enviar"}
            </Button>
          </div>
        </div>
        {sendFeedback ? (
          <p className="mt-2 text-xs text-muted-foreground">{sendFeedback}</p>
        ) : null}
      </DashboardSection>

      <DashboardSection
        title="Mensajes recientes"
        description={`Últimos ${messages.length} mensajes (inbound + outbound)`}
      >
        {isLoading ? (
          <div className="grid gap-2">
            {Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} className="h-10 w-full" />
            ))}
          </div>
        ) : (
          <DataTable<MessageRow>
            columns={[
              { key: "direction", header: "Tipo" },
              { key: "from_to", header: "De → Para" },
              { key: "body", header: "Mensaje" },
              { key: "status", header: "Estado" },
              { key: "created", header: "Cuándo" },
            ]}
            rows={messageRows}
            emptyTitle="Sin mensajes"
            emptyDescription="Cuando lleguen o envíes mensajes, aparecerán aquí."
          />
        )}
      </DashboardSection>

      <DashboardSection
        title="Webhooks"
        description="Auditoría inmutable de cada payload que Meta envía al endpoint /api/v1/whatsapp/webhook"
      >
        {isLoading ? (
          <Skeleton className="h-32 w-full" />
        ) : (
          <DataTable<WebhookRow>
            columns={[
              { key: "event", header: "Tipo" },
              { key: "phone", header: "phone_number_id" },
              { key: "processed", header: "Procesado" },
              { key: "error", header: "Error" },
              { key: "received", header: "Recibido" },
            ]}
            rows={webhookRows}
            emptyTitle="Sin webhooks aún"
            emptyDescription={`Configura el webhook en Meta apuntando a /api/v1/whatsapp/webhook con el hub.verify_token registrado.`}
          />
        )}
      </DashboardSection>
    </div>
  );
}
