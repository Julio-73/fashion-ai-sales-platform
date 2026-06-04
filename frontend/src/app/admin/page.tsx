"use client";

import {
  Banknote,
  Building2,
  CheckCircle2,
  Clock3,
  MessageSquare,
  ShoppingBag,
  UsersRound,
  XCircle
} from "lucide-react";
import { useCallback, useEffect, useState } from "react";

import { t } from "@/lib/i18n";
import { ApiError } from "@/services/api-client";
import * as adminService from "@/services/admin.service";
import { AdminShell } from "@/components/admin/admin-shell";
import { AdminProtectedRoute } from "@/components/admin/admin-protected-route";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { MetricCard } from "@/components/ui/metric-card";
import { DashboardSkeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import type { GlobalDashboard } from "@/types/admin";
import { useAdminStore } from "@/store/admin-store";

const formatter = new Intl.NumberFormat("es-PE");
const money = new Intl.NumberFormat("es-PE", { style: "currency", currency: "USD" });

function DashboardBody() {
  const { accessToken } = useAdminStore();
  const [data, setData] = useState<GlobalDashboard | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!accessToken) {
      return;
    }
    setIsLoading(true);
    setError(null);
    try {
      const response = await adminService.adminDashboard(accessToken);
      setData(response);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError(t.admin.dashboard.errorLoad);
      }
    } finally {
      setIsLoading(false);
    }
  }, [accessToken]);

  useEffect(() => {
    void load();
  }, [load]);

  const D = t.admin.dashboard;

  if (isLoading) {
    return <DashboardSkeleton />;
  }

  if (error || !data) {
    return (
      <div className="rounded-lg border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
        {error ?? D.errorLoad}
        <div className="mt-3">
          <Button type="button" variant="outline" size="sm" onClick={() => void load()}>
            {D.refresh}
          </Button>
        </div>
      </div>
    );
  }

  const metrics = [
    {
      title: D.metricTotalEmpresas,
      value: formatter.format(data.total_empresas),
      icon: Building2,
      footer: (
        <span className="text-xs text-muted-foreground">
          {D.metricEmpresasActivas}: {formatter.format(data.empresas_activas)}
        </span>
      )
    },
    {
      title: D.metricEmpresasActivas,
      value: formatter.format(data.empresas_activas),
      icon: CheckCircle2,
      footer: (
        <span className="text-xs text-muted-foreground">
          {D.metricEmpresasSuspendidas}: {formatter.format(data.empresas_suspendidas)}
        </span>
      )
    },
    {
      title: D.metricEmpresasSuspendidas,
      value: formatter.format(data.empresas_suspendidas),
      icon: XCircle
    },
    {
      title: D.metricEmpresasExpiradas,
      value: formatter.format(data.empresas_expiradas),
      icon: Clock3
    },
    {
      title: D.metricClientesTotales,
      value: formatter.format(data.total_clientes),
      icon: UsersRound
    },
    {
      title: D.metricPedidosTotales,
      value: formatter.format(data.total_pedidos),
      icon: ShoppingBag
    },
    {
      title: D.metricConversacionesTotales,
      value: formatter.format(data.total_conversaciones),
      icon: MessageSquare
    },
    {
      title: D.metricVentasTotales,
      value: money.format(data.total_ventas),
      icon: Banknote
    }
  ];

  return (
    <div className="grid gap-6">
      <header className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-primary">
            {D.eyebrow}
          </p>
          <h1 className="mt-2 text-2xl font-semibold tracking-normal text-foreground md:text-3xl">
            {D.title}
          </h1>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">
            {D.description}
          </p>
        </div>
        <Button type="button" variant="outline" size="sm" onClick={() => void load()}>
          {D.refresh}
        </Button>
      </header>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {metrics.map((metric, index) => (
          <MetricCard
            key={metric.title}
            title={metric.title}
            value={metric.value}
            icon={metric.icon}
            footer={metric.footer}
            delay={index * 0.04}
          />
        ))}
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>{D.planBreakdown}</CardTitle>
          </CardHeader>
          <CardContent>
            <BreakdownList
              items={data.planes_breakdown}
              labelMap={(key) => (t.admin.plan as Record<string, string>)[key] ?? key}
              emptyLabel={D.emptyBreakdown}
            />
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>{D.statusBreakdown}</CardTitle>
          </CardHeader>
          <CardContent>
            <BreakdownList
              items={data.status_breakdown}
              labelMap={(key) =>
                (t.admin.status as Record<string, string>)[key] ?? key
              }
              emptyLabel={D.emptyBreakdown}
            />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function BreakdownList({
  items,
  labelMap,
  emptyLabel = "—"
}: {
  items: Record<string, number> | null | undefined;
  labelMap: (key: string) => string;
  emptyLabel?: string;
}) {
  const safeItems: Record<string, number> = items ?? {};
  const entries = Object.entries(safeItems);
  const total = entries.reduce((acc, [, value]) => acc + (Number.isFinite(value) ? value : 0), 0);
  if (entries.length === 0 || total === 0) {
    return <p className="text-sm text-muted-foreground">{emptyLabel}</p>;
  }
  return (
    <ul className="grid gap-2">
      {entries.map(([key, value]) => {
        const pct = total > 0 ? Math.round((value / total) * 100) : 0;
        return (
          <li key={key} className="flex items-center justify-between gap-3 text-sm">
            <span className="font-medium text-foreground">{labelMap(key)}</span>
            <span className="text-muted-foreground">
              {formatter.format(value)} · {pct}%
            </span>
          </li>
        );
      })}
    </ul>
  );
}

export default function AdminDashboardPage() {
  return (
    <AdminProtectedRoute>
      <AdminShell>
        <DashboardBody />
      </AdminShell>
    </AdminProtectedRoute>
  );
}
