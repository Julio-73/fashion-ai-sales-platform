export type ReportKind =
  | "executive"
  | "pipeline"
  | "crm"
  | "sales"
  | "inventory";

export type ReportFormat = "pdf" | "excel";

export const REPORT_PATHS: Record<ReportKind, { pdf: string; excel: string }> = {
  executive: {
    pdf: "/reporting/executive/pdf",
    excel: "/reporting/executive/excel"
  },
  pipeline: {
    pdf: "/reporting/pipeline/pdf",
    excel: "/reporting/pipeline/excel"
  },
  crm: {
    pdf: "/reporting/crm/pdf",
    excel: "/reporting/crm/excel"
  },
  sales: {
    pdf: "/reporting/sales/pdf",
    excel: "/reporting/sales/excel"
  },
  inventory: {
    pdf: "/reporting/inventory/pdf",
    excel: "/reporting/inventory/excel"
  }
};
