"use client";

import { motion } from "framer-motion";
import {
  AlertTriangle,
  ArrowRight,
  Bot,
  CheckCircle2,
  Clock3,
  MessageSquare,
  PauseCircle,
  PlayCircle,
  Plus,
  RefreshCw,
  Send,
  Sparkles,
  Tag,
  Workflow,
} from "lucide-react";
import { useMemo, useState } from "react";

import { DataTable } from "@/components/data-table/data-table";
import { DashboardSection } from "@/components/layout/dashboard-section";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { MetricCard } from "@/components/ui/metric-card";
import { StatusBadge } from "@/components/ui/status-badge";
import { cn } from "@/lib/utils";

type AutomationStatus = "active" | "paused" | "draft";

type AutomationRule = {
  id: string;
  name: string;
  trigger: string;
  action: string;
  channel: string;
  status: AutomationStatus;
  runsToday: number;
  conversionRate: string;
  lastRun: string;
};

type AutomationTemplate = {
  id: string;
  title: string;
  description: string;
  icon: typeof MessageSquare;
  trigger: string;
  action: string;
};

const statusCopy: Record<AutomationStatus, { label: string; tone: "success" | "warning" | "neutral" }> = {
  active: { label: "Activa", tone: "success" },
  paused: { label: "Pausada", tone: "warning" },
  draft: { label: "Borrador", tone: "neutral" },
};

const rules: AutomationRule[] = [
  {
    id: "new-lead-fast-reply",
    name: "Respuesta inmediata a nuevos leads",
    trigger: "Cliente nuevo escribe por WhatsApp",
    action: "Enviar saludo con IA y pedir preferencia de prenda",
    channel: "WhatsApp",
    status: "active",
    runsToday: 42,
    conversionRate: "18%",
    lastRun: "Hace 8 min",
  },
  {
    id: "hot-lead-follow-up",
    name: "Seguimiento a intención alta",
    trigger: "Lead score supera 80 puntos",
    action: "Crear tarea y sugerir oferta personalizada",
    channel: "CRM + IA",
    status: "active",
    runsToday: 17,
    conversionRate: "31%",
    lastRun: "Hace 21 min",
  },
  {
    id: "abandoned-negotiation",
    name: "Recuperación de negociación dormida",
    trigger: "Sin respuesta por 24 horas",
    action: "Enviar mensaje de urgencia suave",
    channel: "Instagram",
    status: "paused",
    runsToday: 0,
    conversionRate: "12%",
    lastRun: "Ayer",
  },
  {
    id: "vip-tagging",
    name: "Etiquetado automático VIP",
    trigger: "Cliente compra más de 3 veces",
    action: "Agregar etiqueta VIP y activar oferta premium",
    channel: "CRM",
    status: "draft",
    runsToday: 0,
    conversionRate: "-",
    lastRun: "Sin ejecutar",
  },
];

const templates: AutomationTemplate[] = [
  {
    id: "welcome-flow",
    title: "Bienvenida inteligente",
    description: "Clasifica el interés del cliente y responde con una apertura natural.",
    icon: MessageSquare,
    trigger: "Primer mensaje",
    action: "Respuesta IA",
  },
  {
    id: "stock-alert",
    title: "Alerta por stock bajo",
    description: "Detecta productos con alta demanda y prepara mensajes de escasez.",
    icon: AlertTriangle,
    trigger: "Stock crítico",
    action: "Campaña sugerida",
  },
  {
    id: "post-sale",
    title: "Postventa y recompra",
    description: "Programa seguimiento después de una compra y propone productos complementarios.",
    icon: Sparkles,
    trigger: "Venta ganada",
    action: "Upsell",
  },
];

const activity = [
  "La regla de nuevos leads respondió 12 conversaciones en la última hora.",
  "IA detectó 5 conversaciones con intención de compra alta.",
  "Se pausó la recuperación de Instagram para revisar tono comercial.",
  "El flujo VIP está listo para conectar con eventos de compras.",
];

export function AutomationsWorkspace() {
  const [selectedStatus, setSelectedStatus] = useState<AutomationStatus | "all">("all");

  const filteredRules = useMemo(() => {
    if (selectedStatus === "all") return rules;
    return rules.filter((rule) => rule.status === selectedStatus);
  }, [selectedStatus]);

  const activeRules = rules.filter((rule) => rule.status === "active").length;
  const totalRuns = rules.reduce((sum, rule) => sum + rule.runsToday, 0);

  const rows = filteredRules.map((rule) => ({
    rule: (
      <div>
        <p className="font-medium text-foreground">{rule.name}</p>
        <p className="mt-1 text-xs text-muted-foreground">{rule.channel}</p>
      </div>
    ),
    flow: (
      <div className="flex flex-col gap-1 text-sm text-muted-foreground xl:flex-row xl:items-center xl:gap-2">
        <span className="truncate">{rule.trigger}</span>
        <ArrowRight className="hidden h-3.5 w-3.5 shrink-0 text-muted-foreground xl:block" aria-hidden="true" />
        <span className="truncate text-foreground">{rule.action}</span>
      </div>
    ),
    status: <StatusBadge tone={statusCopy[rule.status].tone}>{statusCopy[rule.status].label}</StatusBadge>,
    performance: (
      <div className="text-sm">
        <p className="font-medium text-foreground">{rule.runsToday} ejecuciones</p>
        <p className="text-xs text-muted-foreground">{rule.conversionRate} conversión</p>
      </div>
    ),
    lastRun: rule.lastRun,
  }));

  return (
    <div className="grid gap-6">
      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          title="Reglas activas"
          value={String(activeRules)}
          trend="Operando"
          icon={Workflow}
          footer={<span className="text-xs text-muted-foreground">Automatizaciones listas para responder sin fricción.</span>}
        />
        <MetricCard
          title="Ejecuciones hoy"
          value={String(totalRuns)}
          trend="+14%"
          icon={PlayCircle}
          footer={<span className="text-xs text-muted-foreground">Eventos procesados desde conversaciones y CRM.</span>}
          delay={0.04}
        />
        <MetricCard
          title="Tiempo ahorrado"
          value="6.8 h"
          trend="Estimado"
          icon={Clock3}
          footer={<span className="text-xs text-muted-foreground">Basado en respuestas, tareas y etiquetado automático.</span>}
          delay={0.08}
        />
        <MetricCard
          title="Flujos en riesgo"
          value="1"
          trend="Revisar"
          icon={PauseCircle}
          footer={<span className="text-xs text-muted-foreground">Una regla pausada espera ajuste de tono.</span>}
          delay={0.12}
        />
      </section>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_340px]">
        <DashboardSection
          title="Motor de reglas"
          description="Controla disparadores, acciones y rendimiento de automatizaciones comerciales."
          action={
            <Button type="button">
              <Plus className="h-4 w-4" aria-hidden="true" />
              Nueva regla
            </Button>
          }
        >
          <div className="rounded-lg border bg-card p-4 shadow-sm">
            <div className="mb-4 flex flex-wrap gap-2">
              {(["all", "active", "paused", "draft"] as const).map((status) => (
                <button
                  key={status}
                  type="button"
                  className={cn(
                    "h-9 rounded-md border px-3 text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                    selectedStatus === status
                      ? "border-primary bg-primary text-primary-foreground"
                      : "bg-background text-muted-foreground hover:bg-secondary hover:text-foreground",
                  )}
                  onClick={() => setSelectedStatus(status)}
                >
                  {status === "all" ? "Todas" : statusCopy[status].label}
                </button>
              ))}
            </div>
            <DataTable
              columns={[
                { key: "rule", header: "Regla" },
                { key: "flow", header: "Flujo" },
                { key: "status", header: "Estado" },
                { key: "performance", header: "Rendimiento" },
                { key: "lastRun", header: "Última ejecución" },
              ]}
              rows={rows}
              emptyTitle="Sin reglas"
              emptyDescription="Crea una regla para comenzar a automatizar conversaciones y tareas."
            />
          </div>
        </DashboardSection>

        <DashboardSection
          title="Actividad"
          description="Señales recientes del sistema."
        >
          <div className="grid gap-3">
            {activity.map((item, index) => (
              <motion.div
                key={item}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.24, delay: index * 0.04 }}
                className="rounded-lg border bg-card p-4 shadow-sm"
              >
                <div className="flex gap-3">
                  <span className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-secondary text-primary">
                    <CheckCircle2 className="h-4 w-4" aria-hidden="true" />
                  </span>
                  <p className="text-sm leading-6 text-muted-foreground">{item}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </DashboardSection>
      </div>

      <DashboardSection
        title="Plantillas recomendadas"
        description="Flujos listos para convertir conversaciones de moda en acciones medibles."
      >
        <div className="grid gap-4 md:grid-cols-3">
          {templates.map((template, index) => (
            <motion.div
              key={template.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.28, delay: index * 0.05 }}
            >
              <Card className="h-full transition-shadow hover:shadow-md">
                <CardHeader>
                  <div className="flex items-center justify-between gap-3">
                    <span className="flex h-10 w-10 items-center justify-center rounded-lg border bg-secondary text-primary">
                      <template.icon className="h-4 w-4" aria-hidden="true" />
                    </span>
                    <Button type="button" variant="ghost" size="icon" aria-label={`Crear ${template.title}`}>
                      <Plus className="h-4 w-4" aria-hidden="true" />
                    </Button>
                  </div>
                  <CardTitle>{template.title}</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="min-h-12 text-sm leading-6 text-muted-foreground">{template.description}</p>
                  <div className="mt-4 grid gap-2 text-xs">
                    <div className="flex items-center gap-2 text-muted-foreground">
                      <Tag className="h-3.5 w-3.5" aria-hidden="true" />
                      <span>{template.trigger}</span>
                    </div>
                    <div className="flex items-center gap-2 text-muted-foreground">
                      <Send className="h-3.5 w-3.5" aria-hidden="true" />
                      <span>{template.action}</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>
      </DashboardSection>

      <div className="rounded-lg border bg-card p-5 shadow-sm">
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div className="flex gap-3">
            <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border bg-secondary text-primary">
              <Bot className="h-4 w-4" aria-hidden="true" />
            </span>
            <div>
              <h2 className="text-base font-semibold">Próximo paso del motor</h2>
              <p className="mt-1 max-w-3xl text-sm leading-6 text-muted-foreground">
                Conectar estas reglas al backend permitirá persistencia por empresa, auditoría de ejecuciones y activación real desde WhatsApp, CRM y eventos de IA.
              </p>
            </div>
          </div>
          <Button type="button" variant="outline">
            <RefreshCw className="h-4 w-4" aria-hidden="true" />
            Preparar backend
          </Button>
        </div>
      </div>
    </div>
  );
}
