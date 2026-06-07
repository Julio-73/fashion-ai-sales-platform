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
import { useParams, useRouter } from "next/navigation";

import { t } from "@/lib/i18n";
import { ApiError } from "@/services/api-client";
import { useAuthStore } from "@/store/auth-store";
import { AppShell } from "@/components/layout/app-shell";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Avatar } from "@/components/ui/avatar";
import { StatusPill } from "@/components/ui/status-pill";
import { MetricCard } from "@/components/ui/metric-card";
import { PageHeader } from "@/components/layout/page-header";
import { DashboardContent } from "@/components/layout/dashboard-content";
import { DashboardSection } from "@/components/layout/dashboard-section";
import { EmptyState } from "@/components/feedback/empty-state";
import { Skeleton } from "@/components/ui/skeleton";
import { CustomerLifecycleBadge } from "@/modules/crm/components/customer-lifecycle-badge";
import {
  getCustomer360,
  getCustomerOrders
} from "@/modules/crm/services/crm-api";
import { formatCurrency, formatDate, formatDateTime, formatNumber } from "@/modules/crm/utils/format";
import { cn } from "@/lib/utils";
import type {
  Customer360Summary,
  CustomerOrderHistoryItem
} from "@/types/crm";

const P = t.crm.detail;

const ORDER_STATUS_TONE: Record<string, "destructive" | "success" | "info" | "warning" | "primary" | "neutral"> = {
  cancelled: "destructive",
  delivered: "success",
  confirmed: "info",
  preparing: "warning",
  shipped: "primary",
  pending: "neutral"
};

const ORDER_STATUS_LABELS: Record<string, string> = {
  cancelled: P.orders.cancelled,
  delivered: P.orders.delivered,
  confirmed: P.orders.confirmed,
  preparing: P.orders.preparing,
  shipped: P.orders.shipped,
  pending: P.orders.pending
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
        <PageHeader
          eyebrow={t.crm.page.eyebrow}
          title={summary?.full_name ?? (isLoading ? "Cargando cliente..." : "Cliente")}
          description={
            summary
              ? `${summary.email ?? summary.phone ?? summary.instagram_username ?? t.crm.workspace.fallbackNotSet}`
              : "Perfil 360 del cliente"
          }
          breadcrumbs={[
            { label: "CRM", href: "/dashboard/customers" },
            { label: summary?.full_name ?? "Cliente" }
          ]}
          actions={
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => router.push("/dashboard/customers")}
            >
              <ArrowLeft className="h-4 w-4" aria-hidden="true" />
              {P.back}
            </Button>
          }
        />

        {isLoading ? (
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            {Array.from({ length: 5 }).map((_, i) => (
              <Skeleton
                key={i}
                className="h-32 w-full rounded-xl"
              />
            ))}
          </div>
        ) : null}

        {error ? (
          <div className="rounded-lg border border-destructive-200 bg-destructive-50 px-4 py-3 text-sm text-destructive">
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
            <Card variant="elevated" className="overflow-hidden">
              <div className="relative bg-gradient-to-r from-primary-50 via-purple-50/40 to-cyan-50/40 px-6 py-5">
                <div className="flex flex-wrap items-center gap-4">
                  <Avatar
                    name={summary.full_name}
                    size="xl"
                    className="ring-4 ring-card"
                  />
                  <div className="min-w-0 flex-1">
                    <h2 className="truncate text-xl font-semibold tracking-tight text-foreground">
                      {summary.full_name}
                    </h2>
                    <div className="mt-1 flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
                      {summary.email ? (
                        <span className="inline-flex items-center gap-1">
                          <Mail className="h-3.5 w-3.5" aria-hidden="true" />
                          {summary.email}
                        </span>
                      ) : null}
                      {summary.phone ? (
                        <span className="inline-flex items-center gap-1">
                          <Phone className="h-3.5 w-3.5" aria-hidden="true" />
                          {summary.phone}
                        </span>
                      ) : null}
                      {summary.whatsapp ? (
                        <span className="inline-flex items-center gap-1 text-success">
                          <MessageCircle
                            className="h-3.5 w-3.5"
                            aria-hidden="true"
                          />
                          {summary.whatsapp}
                        </span>
                      ) : null}
                      {summary.instagram_username ? (
                        <span className="inline-flex items-center gap-1 text-pink-600">
                          <Instagram
                            className="h-3.5 w-3.5"
                            aria-hidden="true"
                          />
                          {summary.instagram_username}
                        </span>
                      ) : null}
                    </div>
                  </div>
                  <StatusPill
                    tone={
                      summary.metrics.status === "vip"
                        ? "warning"
                        : summary.metrics.status === "inactivo"
                          ? "destructive"
                          : "success"
                    }
                    size="md"
                  >
                    {summary.metrics.status.toUpperCase()}
                  </StatusPill>
                </div>
              </div>
            </Card>

            <DashboardSection title={P.summary.title}>
              <div className="grid gap-4 md:grid-cols-2">
                <Card>
                  <CardContent className="p-5">
                    <h3 className="text-sm font-semibold tracking-tight text-foreground">
                      {P.summary.contact}
                    </h3>
                    <div className="mt-3 grid gap-2">
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
                        accent="success"
                      />
                      <ContactRow
                        icon={Instagram}
                        label="Instagram"
                        value={summary.instagram_username}
                        accent="primary"
                      />
                    </div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="p-5">
                    <h3 className="text-sm font-semibold tracking-tight text-foreground">
                      Perfil
                    </h3>
                    <div className="mt-3 grid gap-2 text-sm">
                      <InfoRow
                        label={P.summary.leadStatus}
                        value={
                          <span className="font-medium capitalize">
                            {summary.lead_status}
                          </span>
                        }
                      />
                      <InfoRow
                        label={P.summary.source}
                        value={
                          <span className="font-medium">
                            {summary.source ?? P.summary.noSource}
                          </span>
                        }
                      />
                      <InfoRow
                        label={P.summary.registeredAt}
                        value={
                          <span className="font-medium">
                            {formatDate(summary.created_at)}
                          </span>
                        }
                      />
                      <InfoRow
                        label="Estado 360"
                        value={
                          <CustomerLifecycleBadge
                            status={summary.metrics.status}
                          />
                        }
                      />
                    </div>
                  </CardContent>
                </Card>
              </div>
            </DashboardSection>

            <DashboardSection title={P.metrics.title}>
              <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
                <MetricCard
                  icon={ClipboardList}
                  title={P.metrics.orderCount}
                  value={formatNumber(summary.metrics.order_count)}
                  iconTone="info"
                />
                <MetricCard
                  icon={TrendingUp}
                  title={P.metrics.lifetimeValue}
                  value={formatCurrency(summary.metrics.lifetime_value)}
                  iconTone="success"
                />
                <MetricCard
                  icon={TrendingUp}
                  title={P.metrics.averageTicket}
                  value={formatCurrency(summary.metrics.average_ticket)}
                  iconTone="primary"
                />
                <MetricCard
                  icon={Calendar}
                  title={P.metrics.lastPurchase}
                  value={
                    summary.metrics.last_purchase_at
                      ? formatDate(summary.metrics.last_purchase_at)
                      : P.metrics.notAvailable
                  }
                  iconTone="purple"
                  description={
                    summary.metrics.days_since_last_purchase !== null ? (
                      <span>
                        {P.metrics.daysSinceLastPurchase}:{" "}
                        <strong className="text-foreground">
                          {summary.metrics.days_since_last_purchase}
                        </strong>
                      </span>
                    ) : (
                      <span>{P.metrics.daysSinceNever}</span>
                    )
                  }
                />
                <MetricCard
                  icon={Calendar}
                  title={P.metrics.firstPurchase}
                  value={
                    summary.metrics.first_purchase_at
                      ? formatDate(summary.metrics.first_purchase_at)
                      : P.metrics.notAvailable
                  }
                  iconTone="warning"
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
                <Card>
                  <div className="overflow-hidden rounded-lg">
                    <table className="w-full text-sm">
                      <thead className="border-b border-border bg-muted/40 text-left text-xs uppercase tracking-wider text-muted-foreground">
                        <tr>
                          <th className="px-4 py-3 font-medium">
                            {P.orders.tableHeaderOrder}
                          </th>
                          <th className="px-4 py-3 font-medium">
                            {P.orders.tableHeaderDate}
                          </th>
                          <th className="px-4 py-3 font-medium">
                            {P.orders.tableHeaderProduct}
                          </th>
                          <th className="px-4 py-3 text-right font-medium">
                            {P.orders.tableHeaderItems}
                          </th>
                          <th className="px-4 py-3 font-medium">
                            {P.orders.tableHeaderStatus}
                          </th>
                          <th className="px-4 py-3 text-right font-medium">
                            {P.orders.tableHeaderTotal}
                          </th>
                        </tr>
                      </thead>
                      <tbody>
                        {orders.map((order) => (
                          <tr
                            key={order.order_id}
                            className="border-t border-border transition hover:bg-muted/30"
                          >
                            <td className="px-4 py-3 font-medium text-foreground">
                              {order.order_number}
                            </td>
                            <td className="px-4 py-3 text-muted-foreground">
                              {formatDateTime(order.created_at)}
                            </td>
                            <td className="px-4 py-3 text-foreground">
                              {order.primary_product_name || "—"}
                            </td>
                            <td className="px-4 py-3 text-right font-medium text-foreground">
                              {formatNumber(order.items_count)}
                            </td>
                            <td className="px-4 py-3">
                              <StatusPill
                                tone={
                                  ORDER_STATUS_TONE[order.status] ?? "neutral"
                                }
                                size="sm"
                              >
                                {ORDER_STATUS_LABELS[order.status] ??
                                  order.status}
                              </StatusPill>
                            </td>
                            <td className="px-4 py-3 text-right font-semibold text-foreground">
                              {formatCurrency(order.total)}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  <div className="flex items-center justify-between border-t border-border px-2 py-2 text-sm text-muted-foreground">
                    <span className="px-2">
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
                </Card>
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
  value,
  accent
}: {
  icon: typeof Mail;
  label: string;
  value: string | null | undefined;
  accent?: "success" | "primary";
}) {
  return (
    <div
      className={cn(
        "flex items-center gap-3 rounded-lg border border-border bg-background px-3 py-2"
      )}
    >
      <span
        className={cn(
          "flex h-7 w-7 items-center justify-center rounded-md",
          accent === "success" && "bg-success-50 text-success",
          accent === "primary" && "bg-primary-50 text-primary",
          !accent && "bg-muted text-muted-foreground"
        )}
      >
        <Icon className="h-3.5 w-3.5" aria-hidden="true" />
      </span>
      <div className="min-w-0 flex-1">
        <p className="text-[10px] uppercase tracking-wider text-muted-foreground">
          {label}
        </p>
        <p className="truncate text-sm font-medium text-foreground">
          {value || "—"}
        </p>
      </div>
    </div>
  );
}

function InfoRow({
  label,
  value
}: {
  label: string;
  value: React.ReactNode;
}) {
  return (
    <div className="flex items-center justify-between gap-2 border-b border-dashed border-border/60 py-1.5 last:border-0">
      <span className="text-muted-foreground">{label}</span>
      <span className="text-foreground">{value}</span>
    </div>
  );
}
