"use client";

import {
  BarChart3,
  Download,
  FileText,
  LineChart,
  Package,
  UsersRound,
  type LucideIcon
} from "lucide-react";

import { DashboardSection } from "@/components/layout/dashboard-section";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { t } from "@/lib/i18n";

import { ExportReportButtons } from "./export-report-buttons";

const R = t.reporting;

type ReportDef = {
  key: "executive" | "pipeline" | "crm" | "sales" | "inventory";
  title: string;
  description: string;
  icon: LucideIcon;
  tone: "primary" | "success" | "info" | "warning" | "purple";
  preview: Array<{ label: string; value: string; trend: "up" | "down" | "flat" }>;
};

const reports: ReportDef[] = [
  {
    key: "executive",
    title: R.executive,
    description: R.executiveDesc,
    icon: BarChart3,
    tone: "primary",
    preview: [
      { label: "Revenue", value: "$128.4k", trend: "up" },
      { label: "Win rate", value: "32%", trend: "up" },
      { label: "Churn", value: "4.1%", trend: "down" }
    ]
  },
  {
    key: "pipeline",
    title: R.pipeline,
    description: R.pipelineDesc,
    icon: LineChart,
    tone: "info",
    preview: [
      { label: "Abiertos", value: "184", trend: "flat" },
      { label: "Ponderado", value: "$312k", trend: "up" },
      { label: "Avance 30d", value: "+12%", trend: "up" }
    ]
  },
  {
    key: "crm",
    title: R.crm,
    description: R.crmDesc,
    icon: UsersRound,
    tone: "success",
    preview: [
      { label: "Activos", value: "1.247", trend: "up" },
      { label: "VIP", value: "64", trend: "up" },
      { label: "Inactivos", value: "12", trend: "down" }
    ]
  },
  {
    key: "sales",
    title: R.sales,
    description: R.salesDesc,
    icon: FileText,
    tone: "warning",
    preview: [
      { label: "Pedidos", value: "928", trend: "up" },
      { label: "Ticket", value: "$112", trend: "flat" },
      { label: "Recompra", value: "38%", trend: "up" }
    ]
  },
  {
    key: "inventory",
    title: R.inventory,
    description: R.inventoryDesc,
    icon: Package,
    tone: "purple",
    preview: [
      { label: "SKUs", value: "486", trend: "flat" },
      { label: "Stock bajo", value: "12", trend: "down" },
      { label: "Rotación", value: "2.3x", trend: "up" }
    ]
  }
];

const toneClasses: Record<ReportDef["tone"], string> = {
  primary: "bg-primary-50 text-primary",
  success: "bg-success-50 text-success",
  info: "bg-info-50 text-info",
  warning: "bg-warning-50 text-warning",
  purple: "bg-purple-50 text-purple"
};

const trendColors: Record<"up" | "down" | "flat", string> = {
  up: "text-success",
  down: "text-destructive",
  flat: "text-muted-foreground"
};

const trendSymbols: Record<"up" | "down" | "flat", string> = {
  up: "▲",
  down: "▼",
  flat: "▬"
};

export function ReportsWorkspace() {
  return (
    <div className="flex flex-col gap-6">
      <DashboardSection
        title={R.overview}
        description={R.overviewDesc}
        action={
          <span className="inline-flex items-center gap-2 rounded-full border border-border bg-card px-3 py-1 text-xs text-muted-foreground shadow-xs">
            <Download className="h-3.5 w-3.5" aria-hidden="true" />
            {R.readyIn}
          </span>
        }
      >
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {reports.map((r) => {
            const Icon = r.icon;
            return (
              <Card
                key={r.key}
                variant="elevated"
                className="group transition-all hover:-translate-y-0.5 hover:shadow-md"
              >
                <CardHeader className="flex flex-row items-start gap-3 space-y-0">
                  <span
                    className={cn(
                      "flex h-10 w-10 items-center justify-center rounded-lg",
                      toneClasses[r.tone]
                    )}
                  >
                    <Icon className="h-5 w-5" aria-hidden="true" />
                  </span>
                  <div className="flex-1">
                    <CardTitle className="text-base font-semibold tracking-tight">
                      {r.title}
                    </CardTitle>
                    <CardDescription className="mt-1 text-xs leading-5">
                      {r.description}
                    </CardDescription>
                  </div>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="grid grid-cols-3 gap-2 rounded-lg border border-border bg-muted/30 p-2">
                    {r.preview.map((p) => (
                      <div key={p.label} className="px-1.5">
                        <p className="text-[10px] uppercase tracking-wider text-muted-foreground">
                          {p.label}
                        </p>
                        <p className="mt-0.5 text-sm font-semibold tracking-tight text-foreground">
                          {p.value}
                        </p>
                        <p className={cn("text-[10px]", trendColors[p.trend])}>
                          {trendSymbols[p.trend]} 30d
                        </p>
                      </div>
                    ))}
                  </div>
                  <ExportReportButtons
                    report={r.key}
                    pdfLabel={R.pdf}
                    excelLabel={R.excel}
                    className="w-full"
                  />
                </CardContent>
              </Card>
            );
          })}
        </div>
      </DashboardSection>
    </div>
  );
}

export default ReportsWorkspace;
