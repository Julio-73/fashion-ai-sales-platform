"use client";

import { Plus } from "lucide-react";
import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { t } from "@/lib/i18n";
import { ApiError } from "@/services/api-client";
import * as adminService from "@/services/admin.service";
import { AdminProtectedRoute } from "@/components/admin/admin-protected-route";
import { AdminShell } from "@/components/admin/admin-shell";
import { Button } from "@/components/ui/button";
import { Modal } from "@/components/ui/modal";
import { StatusBadge } from "@/components/ui/status-badge";
import { useAdminStore } from "@/store/admin-store";
import type { EmpresaPlan, EmpresaStatus, EmpresaTenant, Paginated } from "@/types/admin";

const PLAN_VALUES: EmpresaPlan[] = ["basic", "pro", "enterprise"];
const STATUS_VALUES: EmpresaStatus[] = ["active", "suspended", "expired"];

function statusTone(status: EmpresaStatus) {
  switch (status) {
    case "active":
      return "success" as const;
    case "suspended":
      return "warning" as const;
    case "expired":
      return "neutral" as const;
    default:
      return "neutral" as const;
  }
}

function TenantsBody() {
  const { accessToken, isSuperAdmin } = useAdminStore();
  const [page, setPage] = useState<Paginated<EmpresaTenant> | null>(null);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [planFilter, setPlanFilter] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isCreateOpen, setCreateOpen] = useState(false);
  const [isMutating, setIsMutating] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [draft, setDraft] = useState({
    nombre: "",
    slug: "",
    plan: "basic" as EmpresaPlan,
    status: "active" as EmpresaStatus,
    logo_url: ""
  });

  const T = t.admin.tenants;
  const limit = 20;

  const load = useCallback(async () => {
    if (!accessToken) {
      return;
    }
    setIsLoading(true);
    setError(null);
    try {
      const response = await adminService.adminListTenants(accessToken, {
        limit,
        offset: 0,
        search: search || undefined,
        status: statusFilter || undefined,
        plan: planFilter || undefined
      });
      setPage(response);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Error");
      }
    } finally {
      setIsLoading(false);
    }
  }, [accessToken, search, statusFilter, planFilter]);

  useEffect(() => {
    void load();
  }, [load]);

  const submitCreate = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!accessToken) {
      return;
    }
    setIsMutating(true);
    setActionError(null);
    try {
      await adminService.adminCreateTenant(accessToken, {
        nombre: draft.nombre,
        slug: draft.slug,
        plan: draft.plan,
        status: draft.status,
        logo_url: draft.logo_url || null
      });
      setCreateOpen(false);
      setDraft({ nombre: "", slug: "", plan: "basic", status: "active", logo_url: "" });
      await load();
    } catch (err) {
      if (err instanceof ApiError) {
        setActionError(err.message);
      } else {
        setActionError(T.errorCreate);
      }
    } finally {
      setIsMutating(false);
    }
  };

  const changeStatus = async (tenant: EmpresaTenant, status: EmpresaStatus) => {
    if (!accessToken) {
      return;
    }
    setActionError(null);
    try {
      await adminService.adminUpdateTenantStatus(accessToken, tenant.id, { status });
      await load();
    } catch (err) {
      if (err instanceof ApiError) {
        setActionError(err.message);
      } else {
        setActionError(T.errorUpdateStatus);
      }
    }
  };

  const items = page?.items ?? [];
  const total = page?.total ?? 0;
  const start = total === 0 ? 0 : 1;
  const end = total === 0 ? 0 : items.length;

  return (
    <div className="grid gap-6">
      <header className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-primary">
            {T.eyebrow}
          </p>
          <h1 className="mt-2 text-2xl font-semibold tracking-normal text-foreground md:text-3xl">
            {T.title}
          </h1>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">
            {T.description}
          </p>
        </div>
        {isSuperAdmin ? (
          <Button type="button" onClick={() => setCreateOpen(true)}>
            <Plus className="h-4 w-4" aria-hidden="true" />
            {T.createButton}
          </Button>
        ) : null}
      </header>

      {actionError ? (
        <div className="rounded-md border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive">
          {actionError}
        </div>
      ) : null}

      <div className="grid gap-3 sm:grid-cols-[1fr_180px_180px]">
        <input
          className="h-10 rounded-md border bg-background px-3 text-sm outline-none transition focus-visible:ring-2 focus-visible:ring-ring"
          type="search"
          placeholder={T.searchPlaceholder}
          value={search}
          onChange={(event) => setSearch(event.target.value)}
        />
        <select
          className="h-10 rounded-md border bg-background px-3 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
          value={statusFilter}
          onChange={(event) => setStatusFilter(event.target.value)}
        >
          <option value="">{T.filterAllStatuses}</option>
          {STATUS_VALUES.map((value) => (
            <option key={value} value={value}>
              {t.admin.status[value]}
            </option>
          ))}
        </select>
        <select
          className="h-10 rounded-md border bg-background px-3 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
          value={planFilter}
          onChange={(event) => setPlanFilter(event.target.value)}
        >
          <option value="">{T.filterAllPlans}</option>
          {PLAN_VALUES.map((value) => (
            <option key={value} value={value}>
              {t.admin.plan[value]}
            </option>
          ))}
        </select>
      </div>

      {error ? (
        <div className="rounded-md border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive">
          {error}
        </div>
      ) : null}

      <div className="overflow-hidden rounded-lg border bg-card shadow-sm">
        <table className="w-full min-w-[820px] text-sm">
          <thead className="border-b bg-secondary/70 text-left text-xs uppercase text-muted-foreground">
            <tr>
              <th className="px-4 py-3 font-semibold">{T.tableHeaderName}</th>
              <th className="px-4 py-3 font-semibold">{T.tableHeaderSlug}</th>
              <th className="px-4 py-3 font-semibold">{T.tableHeaderPlan}</th>
              <th className="px-4 py-3 font-semibold">{T.tableHeaderStatus}</th>
              <th className="px-4 py-3 font-semibold">{T.tableHeaderCreatedAt}</th>
              <th className="px-4 py-3 text-right font-semibold">{T.tableHeaderActions}</th>
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
                  {T.emptyTitle} — {T.emptyDesc}
                </td>
              </tr>
            ) : (
              items.map((tenant) => (
                <tr key={tenant.id} className="border-b last:border-b-0 hover:bg-secondary/40">
                  <td className="px-4 py-3 font-medium text-foreground">{tenant.nombre}</td>
                  <td className="px-4 py-3 text-muted-foreground">{tenant.slug}</td>
                  <td className="px-4 py-3 text-muted-foreground">
                    {t.admin.plan[tenant.plan]}
                  </td>
                  <td className="px-4 py-3">
                    <StatusBadge tone={statusTone(tenant.status)}>
                      {t.admin.status[tenant.status]}
                    </StatusBadge>
                  </td>
                  <td className="px-4 py-3 text-muted-foreground">
                    {new Date(tenant.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <div className="flex justify-end gap-2">
                      <Link
                        href={`/admin/tenants/${tenant.id}`}
                        className="rounded-md border bg-background px-2 py-1 text-xs font-medium hover:bg-secondary"
                      >
                        {T.actionView}
                      </Link>
                      {isSuperAdmin && tenant.status !== "active" ? (
                        <button
                          type="button"
                          onClick={() => void changeStatus(tenant, "active")}
                          className="rounded-md bg-emerald-50 px-2 py-1 text-xs font-medium text-emerald-700 ring-1 ring-emerald-200 hover:bg-emerald-100"
                        >
                          {T.actionActivate}
                        </button>
                      ) : null}
                      {isSuperAdmin && tenant.status !== "suspended" ? (
                        <button
                          type="button"
                          onClick={() => void changeStatus(tenant, "suspended")}
                          className="rounded-md bg-amber-50 px-2 py-1 text-xs font-medium text-amber-700 ring-1 ring-amber-200 hover:bg-amber-100"
                        >
                          {T.actionSuspend}
                        </button>
                      ) : null}
                      {isSuperAdmin && tenant.status !== "expired" ? (
                        <button
                          type="button"
                          onClick={() => void changeStatus(tenant, "expired")}
                          className="rounded-md bg-slate-100 px-2 py-1 text-xs font-medium text-slate-700 ring-1 ring-slate-200 hover:bg-slate-200"
                        >
                          {T.actionExpire}
                        </button>
                      ) : null}
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <p className="text-xs text-muted-foreground">
        {total === 0
          ? T.paginationNone
          : T.paginationShowing
              .replace("{start}", String(start))
              .replace("{end}", String(end))
              .replace("{total}", String(total))}
      </p>

      <Modal
        open={isCreateOpen}
        onOpenChange={(open) => {
          if (!isMutating) {
            setCreateOpen(open);
            setActionError(null);
          }
        }}
        title={T.createTitle}
        description={T.createDescription}
      >
        <form className="grid gap-3" onSubmit={submitCreate}>
          <label className="grid gap-1 text-sm">
            <span className="font-medium">{T.fieldName}</span>
            <input
              className="h-10 rounded-md border bg-background px-3 outline-none focus-visible:ring-2 focus-visible:ring-ring"
              type="text"
              value={draft.nombre}
              onChange={(event) =>
                setDraft((current) => ({ ...current, nombre: event.target.value }))
              }
              minLength={2}
              maxLength={120}
              required
            />
          </label>
          <label className="grid gap-1 text-sm">
            <span className="font-medium">{T.fieldSlug}</span>
            <input
              className="h-10 rounded-md border bg-background px-3 outline-none focus-visible:ring-2 focus-visible:ring-ring"
              type="text"
              value={draft.slug}
              onChange={(event) =>
                setDraft((current) => ({
                  ...current,
                  slug: event.target.value.toLowerCase()
                }))
              }
              minLength={2}
              maxLength={64}
              pattern="[a-z0-9-]+"
              required
            />
          </label>
          <label className="grid gap-1 text-sm">
            <span className="font-medium">{T.fieldPlan}</span>
            <select
              className="h-10 rounded-md border bg-background px-3 outline-none focus-visible:ring-2 focus-visible:ring-ring"
              value={draft.plan}
              onChange={(event) =>
                setDraft((current) => ({
                  ...current,
                  plan: event.target.value as EmpresaPlan
                }))
              }
            >
              {PLAN_VALUES.map((value) => (
                <option key={value} value={value}>
                  {t.admin.plan[value]}
                </option>
              ))}
            </select>
          </label>
          <label className="grid gap-1 text-sm">
            <span className="font-medium">{T.fieldStatus}</span>
            <select
              className="h-10 rounded-md border bg-background px-3 outline-none focus-visible:ring-2 focus-visible:ring-ring"
              value={draft.status}
              onChange={(event) =>
                setDraft((current) => ({
                  ...current,
                  status: event.target.value as EmpresaStatus
                }))
              }
            >
              {STATUS_VALUES.map((value) => (
                <option key={value} value={value}>
                  {t.admin.status[value]}
                </option>
              ))}
            </select>
          </label>
          <label className="grid gap-1 text-sm">
            <span className="font-medium">{T.fieldLogo}</span>
            <input
              className="h-10 rounded-md border bg-background px-3 outline-none focus-visible:ring-2 focus-visible:ring-ring"
              type="url"
              placeholder="https://cdn.example.com/logo.png"
              value={draft.logo_url}
              onChange={(event) =>
                setDraft((current) => ({ ...current, logo_url: event.target.value }))
              }
            />
            <span className="text-xs text-muted-foreground">{T.fieldLogoHint}</span>
          </label>
          {actionError ? (
            <div className="rounded-md border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive">
              {actionError}
            </div>
          ) : null}
          <div className="mt-2 flex justify-end gap-2">
            <Button
              type="button"
              variant="outline"
              onClick={() => setCreateOpen(false)}
              disabled={isMutating}
            >
              {T.cancel}
            </Button>
            <Button type="submit" disabled={isMutating}>
              {isMutating ? T.saving : T.save}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}

export default function AdminTenantsPage() {
  return (
    <AdminProtectedRoute>
      <AdminShell>
        <TenantsBody />
      </AdminShell>
    </AdminProtectedRoute>
  );
}
