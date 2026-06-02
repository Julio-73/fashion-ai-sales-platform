"use client";

import { useEffect, useState } from "react";
import {
  ArrowLeft,
  Calendar,
  ClipboardList,
  Instagram,
  Mail,
  MessageCircle,
  Phone,
  TrendingUp,
  UserRound
} from "lucide-react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";

import { t } from "@/lib/i18n";
import { ApiError } from "@/services/api-client";
import { useAuthStore } from "@/store/auth-store";
import { AppShell } from "@/components/layout/app-shell";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { DashboardContent } from "@/components/layout/dashboard-content";
import { DashboardHeader } from "@/components/layout/dashboard-header";
import { DashboardSection } from "@/components/layout/dashboard-section";
import { EmptyState } from "@/components/feedback/empty-state";
import { Skeleton } from "@/components/ui/skeleton";
import { CustomerLifecycleBadge } from "@/modules/crm/components/customer-lifecycle-badge";
import {
  getCustomer360,
  getCustomerOrders
} from "@/modules/crm/services/crm-api";
import { formatCurrency, formatDate, formatDateTime, formatNumber } from "@/modules/crm/utils/format";
import type {
  Customer360Summary,
  CustomerOrderHistoryItem
} from "@/types/crm";

const P = t.crm.detail;

const ORDER_STATUS_LABELS: Record<string, string> = {
  cancelled: P.orders.cancelled,
  delivered: P.orders.delivered,
  confirmed: P.orders.confirmed,
  preparing: P.orders.preparing,
  shipped: P.orders.shipped,
  pending: P.orders.pending
};

const ORDER_STATUS_TONE: Record<string, string> = {
  cancelled: "bg-rose-50 text-rose-700 ring-rose-200",
  delivered: "bg-emerald-50 text-emerald-700 ring-emerald-200",
  confirmed: "bg-blue-50 text-blue-700 ring-blue-200",
  preparing: "bg-amber-50 text-amber-700 ring-amber-200",
  shipped: "bg-indigo-50 text-indigo-700 ring-indigo-200",
  pending: "bg-slate-100 text-slate-700 ring-slate-200"
};

export default function CustomerDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const { accessToken, refreshSession } = useAuthStore();
  const [summary, setSummary] = useState<Customer360Summary | null>(null);
  const [orders, setOrders] = useState<CustomerOrderHistoryItem[]>([]);
  const [ordersTotal, setOrdersTotal] = useState(0);
  const [ordersOffset, setOrdersOffset] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const ordersLimit = 8;

  useEffect(() => {
    if (!accessToken || !params?.id) return;
    loadCustomer();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [accessToken, params?.id]);

  useEffect(() => {
    if (!accessToken || !params?.id) return;
    loadOrders(ordersOffset, false);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [accessToken, params?.id, ordersOffset]);

  async function loadCustomer(retried = false) {
    if (!accessToken || !params?.id) return;
    setIsLoading(true);
    setError(null);
    setNotFound(false);
    try {
      const data = await getCustomer360(accessToken, params.id);
      setSummary(data);
    } catch (err) {
      if (err instanceof ApiError && err.status === 404) {
        setNotFound(true);
        return;
      }
      if (!retried && err instanceof ApiError && err.status === 401) {
        try {
          await refreshSession();
        } catch {
          setError(P.errorLoad);
          return;
        }
        return loadCustomer(true);
      }
      setError(P.errorLoad);
    } finally {
      setIsLoading(false);
    }
  }

  async function loadOrders(offset: number, retried: boolean) {
    if (!accessToken || !params?.id) return;
    try {
      const data = await getCustomerOrders(
        accessToken,
        params.id,
        ordersLimit,
        offset
      );
      setOrders(data.items);
      setOrdersTotal(data.total);
    } catch (err) {
      if (!retried && err instanceof ApiError && err.status === 401) {
        try {
          await refreshSession();
        } catch {
          setError(P.errorLoadOrders);
          return;
        }
        return loadOrders(offset, true);
      }
      setError(P.errorLoadOrders);
    }
  }

  return (
    <AppShell>
      <DashboardContent>
        <div className="mb-4 flex items-center gap-3">
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={() => router.push("/dashboard/customers")}
          >
            <ArrowLeft className="h-4 w-4" aria-hidden="true" />
            {P.back}
          </Button>
        </div>
        <DashboardHeader
          eyebrow={t.crm.page.eyebrow}
          title={
            summary?.full_name ?? (isLoading ? "Cargando cliente..." : "Cliente")
          }
          description={
            summary
              ? `${summary.email ?? summary.phone ?? summary.instagram_username ?? ""}`
              : "Perfil 360 del cliente"
          }
        />

        {isLoading ? (
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="rounded-lg border bg-card p-5 shadow-sm">
                <Skeleton className="h-4 w-24" />
                <Skeleton className="mt-5 h-8 w-32" />
              </div>
            ))}
          </div>
        ) : null}

        {error ? (
          <div className="rounded-lg border border-destructive/25 bg-destructive/10 px-4 py-3 text-sm text-destructive">
            {error}
          </div>
        ) : null}

        {notFound ? (
          <EmptyState
            icon={UserRound}
            title={P.notFoundTitle}
            description={P.notFoundDesc}
            action={{
              label: P.back,
              onClick: () => router.push("/dashboard/customers")
            }}
          />
        ) : null}

        {!isLoading && !notFound && summary ? (
          <div className="grid gap-6">
            <DashboardSection title={P.summary.title}>
              <div className="grid gap-4 md:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
                <Card>
                  <CardHeader>
                    <CardTitle>{P.summary.contact}</CardTitle>
                  </CardHeader>
                  <CardContent className="grid gap-3">
                    <ContactRow
                      icon={Mail}
                      label="Email"
                      value={summary.email}
                    />
                    <ContactRow
                      icon={Phone}
                      label="Teléfono"
                      value={summary.phone}
                    />
                    <ContactRow
                      icon={MessageCircle}
                      label="WhatsApp"
                      value={summary.whatsapp}
                    />
                    <ContactRow
                      icon={Instagram}
                      label="Instagram"
                      value={summary.instagram_username}
                    />
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader>
                    <CardTitle>Perfil</CardTitle>
                  </CardHeader>
                  <CardContent className="grid gap-3 text-sm">
                    <div className="flex items-center justify-between">
                      <span className="text-muted-foreground">
                        {P.summary.leadStatus}
                      </span>
                      <span className="font-medium capitalize">
                        {summary.lead_status}
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-muted-foreground">
                        {P.summary.source}
                      </span>
                      <span className="font-medium">
                        {summary.source ?? P.summary.noSource}
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-muted-foreground">
                        {P.summary.registeredAt}
                      </span>
                      <span className="font-medium">
                        {formatDate(summary.created_at)}
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-muted-foreground">Estado 360</span>
                      <CustomerLifecycleBadge status={summary.metrics.status} />
                    </div>
                  </CardContent>
                </Card>
              </div>
            </DashboardSection>

            <DashboardSection title={P.metrics.title}>
              <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
                <MetricTile
                  icon={ClipboardList}
                  label={P.metrics.orderCount}
                  value={formatNumber(summary.metrics.order_count)}
                />
                <MetricTile
                  icon={TrendingUp}
                  label={P.metrics.lifetimeValue}
                  value={formatCurrency(summary.metrics.lifetime_value)}
                />
                <MetricTile
                  icon={TrendingUp}
                  label={P.metrics.averageTicket}
                  value={formatCurrency(summary.metrics.average_ticket)}
                />
                <MetricTile
                  icon={Calendar}
                  label={P.metrics.lastPurchase}
                  value={
                    summary.metrics.last_purchase_at
                      ? formatDate(summary.metrics.last_purchase_at)
                      : P.metrics.notAvailable
                  }
                  footer={
                    summary.metrics.days_since_last_purchase !== null ? (
                      <span className="text-xs text-muted-foreground">
                        {P.metrics.daysSinceLastPurchase}:{" "}
                        <strong className="text-foreground">
                          {summary.metrics.days_since_last_purchase}
                        </strong>
                      </span>
                    ) : (
                      <span className="text-xs text-muted-foreground">
                        {P.metrics.daysSinceNever}
                      </span>
                    )
                  }
                />
                <MetricTile
                  icon={Calendar}
                  label={P.metrics.firstPurchase}
                  value={
                    summary.metrics.first_purchase_at
                      ? formatDate(summary.metrics.first_purchase_at)
                      : P.metrics.notAvailable
                  }
                />
              </div>
            </DashboardSection>

            <DashboardSection
              title={P.orders.title}
              description={
                ordersTotal > 0
                  ? P.orders.paginationShowing
                      .replace("{start}", String(ordersOffset + 1))
                      .replace("{end}", String(ordersOffset + orders.length))
                      .replace("{total}", String(ordersTotal))
                  : P.orders.paginationNone
              }
            >
              {ordersTotal === 0 ? (
                <EmptyState
                  icon={ClipboardList}
                  title={P.orders.emptyTitle}
                  description={P.orders.emptyDesc}
                />
              ) : (
                <>
                  <div className="overflow-hidden rounded-lg border bg-card shadow-sm">
                    <table className="w-full text-sm">
                      <thead className="bg-muted/50 text-left text-xs uppercase tracking-wide text-muted-foreground">
                        <tr>
                          <th className="px-4 py-3">
                            {P.orders.tableHeaderOrder}
                          </th>
                          <th className="px-4 py-3">
                            {P.orders.tableHeaderDate}
                          </th>
                          <th className="px-4 py-3">
                            {P.orders.tableHeaderProduct}
                          </th>
                          <th className="px-4 py-3 text-right">
                            {P.orders.tableHeaderItems}
                          </th>
                          <th className="px-4 py-3">
                            {P.orders.tableHeaderStatus}
                          </th>
                          <th className="px-4 py-3 text-right">
                            {P.orders.tableHeaderTotal}
                          </th>
                        </tr>
                      </thead>
                      <tbody>
                        {orders.map((order) => (
                          <tr
                            key={order.order_id}
                            className="border-t hover:bg-muted/30"
                          >
                            <td className="px-4 py-3 font-medium">
                              {order.order_number}
                            </td>
                            <td className="px-4 py-3 text-muted-foreground">
                              {formatDateTime(order.created_at)}
                            </td>
                            <td className="px-4 py-3">
                              {order.primary_product_name || "—"}
                            </td>
                            <td className="px-4 py-3 text-right">
                              {formatNumber(order.items_count)}
                            </td>
                            <td className="px-4 py-3">
                              <span
                                className={`inline-flex rounded-md px-2 py-1 text-xs font-medium ring-1 ${
                                  ORDER_STATUS_TONE[order.status] ??
                                  "bg-slate-100 text-slate-700 ring-slate-200"
                                }`}
                              >
                                {ORDER_STATUS_LABELS[order.status] ??
                                  order.status}
                              </span>
                            </td>
                            <td className="px-4 py-3 text-right font-medium">
                              {formatCurrency(order.total)}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  <div className="flex items-center justify-between pt-2 text-sm text-muted-foreground">
                    <span>
                      {P.orders.paginationShowing
                        .replace("{start}", String(ordersOffset + 1))
                        .replace("{end}", String(ordersOffset + orders.length))
                        .replace("{total}", String(ordersTotal))}
                    </span>
                    <div className="flex gap-2">
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        disabled={ordersOffset === 0}
                        onClick={() =>
                          setOrdersOffset((c) => Math.max(0, c - ordersLimit))
                        }
                      >
                        {P.orders.previous}
                      </Button>
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        disabled={ordersOffset + ordersLimit >= ordersTotal}
                        onClick={() =>
                          setOrdersOffset((c) => c + ordersLimit)
                        }
                      >
                        {P.orders.next}
                      </Button>
                    </div>
                  </div>
                </>
              )}
            </DashboardSection>
          </div>
        ) : null}
      </DashboardContent>
    </AppShell>
  );
}

function ContactRow({
  icon: Icon,
  label,
  value
}: {
  icon: typeof Mail;
  label: string;
  value: string | null | undefined;
}) {
  return (
    <div className="flex items-center gap-3 rounded-lg border bg-background px-3 py-2">
      <Icon className="h-4 w-4 text-muted-foreground" aria-hidden="true" />
      <div className="min-w-0 flex-1">
        <p className="text-xs text-muted-foreground">{label}</p>
        <p className="truncate text-sm font-medium">{value || "—"}</p>
      </div>
    </div>
  );
}

function MetricTile({
  icon: Icon,
  label,
  value,
  footer
}: {
  icon: typeof Calendar;
  label: string;
  value: string;
  footer?: React.ReactNode;
}) {
  return (
    <div className="rounded-lg border bg-card p-5 shadow-sm">
      <div className="flex items-center justify-between">
        <p className="text-xs uppercase tracking-wide text-muted-foreground">
          {label}
        </p>
        <div className="flex h-8 w-8 items-center justify-center rounded-lg border bg-secondary text-primary">
          <Icon className="h-4 w-4" aria-hidden="true" />
        </div>
      </div>
      <p className="mt-4 text-xl font-semibold tracking-tight">{value}</p>
      {footer ? <div className="mt-3">{footer}</div> : null}
    </div>
  );
}
