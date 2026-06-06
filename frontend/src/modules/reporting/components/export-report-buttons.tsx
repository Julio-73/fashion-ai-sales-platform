"use client";

import { useState } from "react";

import { FileDown, FileSpreadsheet, Loader2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { ApiError } from "@/services/api-client";
import { useAuthStore } from "@/store/auth-store";

import { downloadReport } from "../services/reporting-api";
import { ReportKind } from "../types";

type ExportReportButtonsProps = {
  report: ReportKind;
  pdfLabel?: string;
  excelLabel?: string;
  variant?: "default" | "outline" | "ghost" | "secondary";
  size?: "default" | "sm" | "icon";
  className?: string;
};

const DEFAULT_PDF_LABEL = "Exportar PDF";
const DEFAULT_EXCEL_LABEL = "Exportar Excel";

export function ExportReportButtons({
  report,
  pdfLabel = DEFAULT_PDF_LABEL,
  excelLabel = DEFAULT_EXCEL_LABEL,
  variant = "outline",
  size = "sm",
  className
}: ExportReportButtonsProps) {
  const authStore = useAuthStore();
  const accessToken = authStore.accessToken ?? undefined;
  const [busy, setBusy] = useState<"pdf" | "excel" | null>(null);
  const [status, setStatus] = useState<{ kind: "success" | "error"; message: string } | null>(null);

  const onExport = async (format: "pdf" | "excel") => {
    if (busy) return;
    setBusy(format);
    setStatus(null);
    try {
      await downloadReport(report, format, { accessToken });
      setStatus({
        kind: "success",
        message:
          format === "pdf"
            ? "Reporte PDF descargado correctamente."
            : "Reporte Excel descargado correctamente."
      });
    } catch (error) {
      const message =
        error instanceof ApiError
          ? error.message
          : error instanceof Error
            ? error.message
            : "No se pudo generar el reporte.";
      setStatus({ kind: "error", message });
    } finally {
      setBusy(null);
    }
  };

  return (
    <div className={className ?? "flex flex-col items-stretch gap-2 sm:flex-row sm:items-center"}>
      <div className="flex flex-wrap items-center gap-2">
        <Button
          type="button"
          variant={variant}
          size={size}
          onClick={() => onExport("pdf")}
          disabled={busy !== null}
          aria-label={pdfLabel}
        >
          {busy === "pdf" ? (
            <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
          ) : (
            <FileDown className="h-4 w-4" aria-hidden="true" />
          )}
          {pdfLabel}
        </Button>
        <Button
          type="button"
          variant={variant}
          size={size}
          onClick={() => onExport("excel")}
          disabled={busy !== null}
          aria-label={excelLabel}
        >
          {busy === "excel" ? (
            <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
          ) : (
            <FileSpreadsheet className="h-4 w-4" aria-hidden="true" />
          )}
          {excelLabel}
        </Button>
      </div>
      {status ? (
        <span
          role="status"
          aria-live="polite"
          className={
            status.kind === "success"
              ? "text-xs font-medium text-emerald-600"
              : "text-xs font-medium text-red-600"
          }
        >
          {status.message}
        </span>
      ) : null}
    </div>
  );
}

export default ExportReportButtons;
