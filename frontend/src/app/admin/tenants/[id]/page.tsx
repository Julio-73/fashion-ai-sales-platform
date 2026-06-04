"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { t } from "@/lib/i18n";
import { ApiError } from "@/services/api-client";
import * as adminService from "@/services/admin.service";
import { AdminProtectedRoute } from "@/components/admin/admin-protected-route";
import { AdminShell } from "@/components/admin/admin-shell";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { StatusBadge } from "@/components/ui/status-badge";
import { useAdminStore } from "@/store/admin-store";
import type { EmpresaStatus, EmpresaTenant } from "@/types/admin";

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

function DetailBody() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const { accessToken, isSuperAdmin } = useAdminStore();
  const [tenant, setTenant] = useState<EmpresaTenant | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [isMutating, setIsMutating] = useState(false);

  const T = t.admin.detail;

  const load = useCallback(async () => {
    if (!accessToken || !params?.id) {
      return;
    }
    setIsLoading(true);
    setError(null);
    try {
      const response = await adminService.adminGetTenant(accessToken, params.id);
      setTenant(response);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.status === 404 ? T.notFoundDesc : err.message);
      } else {
        setError(T.errorLoad);
      }
    } finally {
      setIsLoading(false);
    }
  }, [accessToken, params?.id, T.errorLoad, T.notFoundDesc]);

  useEffect(() => {
    void load();
  }, [load]);

  const changeStatus = async (status: EmpresaStatus) => {
    if (!accessToken || !tenant) {
      return;
    }
    setActionError(null);
    setIsMutating(true);
    try {
      const updated = await adminService.adminUpdateTenantStatus(accessToken, tenant.id, {
        status
      });
      setTenant(updated);
    } catch (err) {
      if (err instanceof ApiError) {
        setActionError(err.message);
      } else {
        setActionError(T.errorUpdate);
      }
    } finally {
      setIsMutating(false);
    }
  };

  if (isLoading) {
    return <p className="text-sm text-muted-foreground">{t.admin.dashboard.loading}</p>;
  }

  if (error || !tenant) {
    return (
      <div className="rounded-lg border bg-card p-6 text-center shadow-sm">
        <h1 className="text-lg font-semibold text-card-foreground">
          {T.notFoundTitle}
        </h1>
        <p className="mt-2 text-sm text-muted-foreground">{error ?? T.notFoundDesc}</p>
        <div className="mt-4">
          <Button asChild type="button" variant="outline">
            <Link href="/admin/tenants">{T.backToList}</Link>
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="grid gap-6">
      <div>
        <Link
          href="/admin/tenants"
          className="text-xs font-medium text-primary hover:underline"
        >
          {T.backToList}
        </Link>
        <h1 className="mt-2 text-2xl font-semibold tracking-normal text-foreground md:text-3xl">
          {tenant.nombre}
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">/{tenant.slug}</p>
      </div>

      {actionError ? (
        <div className="rounded-md border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive">
          {actionError}
        </div>
      ) : null}

      <div className="grid gap-4 lg:grid-cols-[2fr_1fr]">
        <Card>
          <CardHeader>
            <CardTitle>{T.summaryTitle}</CardTitle>
          </CardHeader>
          <CardContent>
            <dl className="grid grid-cols-1 gap-3 text-sm sm:grid-cols-2">
              <Field label={T.fieldName} value={tenant.nombre} />
              <Field label={T.fieldSlug} value={tenant.slug} />
              <Field label={T.fieldPlan} value={t.admin.plan[tenant.plan]} />
              <Field
                label={T.fieldStatus}
                value={
                  <StatusBadge tone={statusTone(tenant.status)}>
                    {t.admin.status[tenant.status]}
                  </StatusBadge>
                }
              />
              <Field
                label={T.fieldLogo}
                value={
                  tenant.logo_url ? (
                    <a
                      href={tenant.logo_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-primary underline"
                    >
                      {tenant.logo_url}
                    </a>
                  ) : (
                    <span className="text-muted-foreground">—</span>
                  )
                }
              />
              <Field
                label={T.fieldCreatedAt}
                value={new Date(tenant.created_at).toLocaleString()}
              />
              <Field
                label={T.fieldUpdatedAt}
                value={new Date(tenant.updated_at).toLocaleString()}
              />
            </dl>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>{T.actionsTitle}</CardTitle>
          </CardHeader>
          <CardContent>
            {!isSuperAdmin ? (
              <p className="text-sm text-muted-foreground">
                {t.admin.protected.forbiddenDesc}
              </p>
            ) : (
              <div className="grid gap-2">
                {STATUS_VALUES.map((status) => (
                  <Button
                    key={status}
                    type="button"
                    variant={tenant.status === status ? "default" : "outline"}
                    disabled={isMutating || tenant.status === status}
                    onClick={() => void changeStatus(status)}
                  >
                    {status === "active"
                      ? T.activate
                      : status === "suspended"
                        ? T.suspend
                        : T.expire}
                  </Button>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function Field({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div>
      <dt className="text-xs uppercase tracking-wide text-muted-foreground">{label}</dt>
      <dd className="mt-1 text-sm text-foreground">{value}</dd>
    </div>
  );
}

export default function AdminTenantDetailPage() {
  return (
    <AdminProtectedRoute>
      <AdminShell>
        <DetailBody />
      </AdminShell>
    </AdminProtectedRoute>
  );
}
