"use client";

import { useCallback, useEffect, useState } from "react";

import { t } from "@/lib/i18n";
import { ApiError } from "@/services/api-client";
import * as adminService from "@/services/admin.service";
import { AdminProtectedRoute } from "@/components/admin/admin-protected-route";
import { AdminShell } from "@/components/admin/admin-shell";
import { useAdminStore } from "@/store/admin-store";
import type { AdminAuditEntry, Paginated } from "@/types/admin";

const ACTION_OPTIONS = [
  "company_created",
  "company_updated",
  "company_suspended",
  "company_activated",
  "company_expired"
];

const formatter = new Intl.DateTimeFormat("es-PE", {
  dateStyle: "short",
  timeStyle: "medium"
});

function AuditBody() {
  const { accessToken } = useAdminStore();
  const [page, setPage] = useState<Paginated<AdminAuditEntry> | null>(null);
  const [actionFilter, setActionFilter] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const A = t.admin.audit;

  const load = useCallback(async () => {
    if (!accessToken) {
      return;
    }
    setIsLoading(true);
    setError(null);
    try {
      const response = await adminService.adminListAudit(accessToken, {
        limit: 50,
        offset: 0,
        action: actionFilter || undefined
      });
      setPage(response);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError(A.errorLoad);
      }
    } finally {
      setIsLoading(false);
    }
  }, [accessToken, actionFilter, A.errorLoad]);

  useEffect(() => {
    void load();
  }, [load]);

  const items = page?.items ?? [];
  const total = page?.total ?? 0;
  const end = items.length;

  return (
    <div className="grid gap-6">
      <header>
        <p className="text-xs font-semibold uppercase tracking-wide text-primary">
          {A.eyebrow}
        </p>
        <h1 className="mt-2 text-2xl font-semibold tracking-normal text-foreground md:text-3xl">
          {A.title}
        </h1>
        <p className="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">
          {A.description}
        </p>
      </header>

      <div className="grid gap-3 sm:grid-cols-[280px_auto]">
        <select
          className="h-10 rounded-md border bg-background px-3 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
          value={actionFilter}
          onChange={(event) => setActionFilter(event.target.value)}
        >
          <option value="">{A.filterAllActions}</option>
          {ACTION_OPTIONS.map((value) => (
            <option key={value} value={value}>
              {value}
            </option>
          ))}
        </select>
      </div>

      {error ? (
        <div className="rounded-md border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive">
          {error}
        </div>
      ) : null}

      <div className="overflow-x-auto rounded-lg border bg-card shadow-sm">
        <table className="w-full min-w-[820px] text-sm">
          <thead className="border-b bg-secondary/70 text-left text-xs uppercase text-muted-foreground">
            <tr>
              <th className="px-4 py-3 font-semibold">{A.tableHeaderWhen}</th>
              <th className="px-4 py-3 font-semibold">{A.tableHeaderAction}</th>
              <th className="px-4 py-3 font-semibold">{A.tableHeaderAdmin}</th>
              <th className="px-4 py-3 font-semibold">{A.tableHeaderTarget}</th>
              <th className="px-4 py-3 font-semibold">{A.tableHeaderIp}</th>
              <th className="px-4 py-3 font-semibold">{A.tableHeaderDetails}</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              Array.from({ length: 4 }).map((_, index) => (
                <tr key={index} className="border-b last:border-b-0">
                  <td colSpan={6} className="px-4 py-3 text-muted-foreground">
                    {t.admin.dashboard.loading}
                  </td>
                </tr>
              ))
            ) : items.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-4 py-10 text-center text-muted-foreground">
                  {A.emptyTitle} — {A.emptyDesc}
                </td>
              </tr>
            ) : (
              items.map((entry) => (
                <tr key={entry.id} className="border-b last:border-b-0 align-top">
                  <td className="whitespace-nowrap px-4 py-3 text-muted-foreground">
                    {formatter.format(new Date(entry.created_at))}
                  </td>
                  <td className="px-4 py-3 font-mono text-xs">{entry.action}</td>
                  <td className="px-4 py-3 text-muted-foreground">
                    {entry.admin_email ?? entry.admin_user_id}
                  </td>
                  <td className="px-4 py-3 text-muted-foreground">
                    {entry.target_empresa_id ?? "—"}
                  </td>
                  <td className="px-4 py-3 text-muted-foreground">{entry.ip_address ?? "—"}</td>
                  <td className="px-4 py-3">
                    {entry.details ? (
                      <pre className="max-w-md overflow-x-auto whitespace-pre-wrap text-xs text-muted-foreground">
                        {JSON.stringify(entry.details, null, 0)}
                      </pre>
                    ) : (
                      <span className="text-muted-foreground">—</span>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <p className="text-xs text-muted-foreground">
        {total === 0
          ? A.paginationNone
          : A.paginationShowing
              .replace("{start}", "1")
              .replace("{end}", String(end))
              .replace("{total}", String(total))}
      </p>
    </div>
  );
}

export default function AdminAuditPage() {
  return (
    <AdminProtectedRoute>
      <AdminShell>
        <AuditBody />
      </AdminShell>
    </AdminProtectedRoute>
  );
}
