import { apiDownload, ApiDownloadResult, triggerBrowserDownload } from "@/services/api-client";

import { ReportFormat, ReportKind, REPORT_PATHS } from "../types";

export type DownloadReportOptions = {
  accessToken?: string;
};

export type DownloadReportResult = ApiDownloadResult;

export async function downloadReport(
  kind: ReportKind,
  format: ReportFormat,
  options: DownloadReportOptions = {}
): Promise<DownloadReportResult> {
  const path = REPORT_PATHS[kind][format];
  const result = await apiDownload(path, { accessToken: options.accessToken });
  triggerBrowserDownload(result.blob, result.filename);
  return result;
}
