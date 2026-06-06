"use client";

import { BarChart3, Download, FileText, LineChart, Package, UsersRound } from "lucide-react";

import { DashboardSection } from "@/components/layout/dashboard-section";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { t } from "@/lib/i18n";

import { ExportReportButtons } from "./export-report-buttons";

const R = t.reporting;

const reports: Array<{
  key: "executive" | "pipeline" | "crm" | "sales" | "inventory";
  title: string;
  description: string;
  icon: typeof BarChart3;
}> = [
  { key: "executive", title: R.executive, description: R.executiveDesc, icon: BarChart3 },
  { key: "pipeline", title: R.pipeline, description: R.pipelineDesc, icon: LineChart },
  { key: "crm", title: R.crm, description: R.crmDesc, icon: UsersRound },
  { key: "sales", title: R.sales, description: R.salesDesc, icon: FileText },
  { key: "inventory", title: R.inventory, description: R.inventoryDesc, icon: Package }
];

export function ReportsWorkspace() {
  return (
    <div className="flex flex-col gap-6">
      <DashboardSection
        title={R.overview}
        description={R.overviewDesc}
        action={
          <span className="inline-flex items-center gap-2 text-xs text-muted-foreground">
            <Download className="h-4 w-4" aria-hidden="true" />
            {R.readyIn}
          </span>
        }
      >
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {reports.map((r) => {
            const Icon = r.icon;
            return (
              <Card key={r.key} className="border-border/60 bg-card/40">
                <CardHeader className="flex flex-row items-start gap-3 space-y-0">
                  <span className="rounded-md bg-primary/10 p-2 text-primary">
                    <Icon className="h-5 w-5" aria-hidden="true" />
                  </span>
                  <div className="flex-1">
                    <CardTitle className="text-base font-semibold">{r.title}</CardTitle>
                    <CardDescription className="mt-1 text-xs leading-5">
                      {r.description}
                    </CardDescription>
                  </div>
                </CardHeader>
                <CardContent>
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
