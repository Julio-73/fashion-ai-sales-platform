"use client";

import {
  Filter,
  Search,
  SlidersHorizontal,
  Sparkles,
  Star,
  UserPlus,
  UsersRound
} from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";

import { t } from "@/lib/i18n";
import { ApiError } from "@/services/api-client";
import { useAuthStore } from "@/store/auth-store";
import { DataTable } from "@/components/data-table/data-table";
import { EmptyState } from "@/components/feedback/empty-state";
import { DashboardSection } from "@/components/layout/dashboard-section";
import { Button } from "@/components/ui/button";
import { MetricCard } from "@/components/ui/metric-card";
import { Skeleton } from "@/components/ui/skeleton";
import { Avatar } from "@/components/ui/avatar";
import { StatusPill } from "@/components/ui/status-pill";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { CustomerLifecycleBadge } from "@/modules/crm/components/customer-lifecycle-badge";
import {
  getCustomerMetrics,
  listCustomer360
} from "@/modules/crm/services/crm-api";
import { formatCurrency, formatDate, formatNumber } from "@/modules/crm/utils/format";
import type {
  CrmSortBy,
  CrmStatusFilter,
  Customer360Summary,
  CustomerAggregateMetrics
} from "@/types/crm";

const W = t.crm.workspace;
const M = t.crm.metrics;

const STATUS_FILTERS: CrmStatusFilter[] = [
  "all",
  "nuevo",
  "activo",
  "recurrente",
  "vip",
  "inactivo"
];

const SORT_OPTIONS: Array<{ value: CrmSortBy; label: string }> = [
  { value: "created_at", label: W.sortCreatedAt },
  { value: "full_name", label: W.sortFullName },
  { value: "lifetime_value", label: W.sortLifetimeValue },
  { value: "last_purchase_at", label: W.sortLastPurchase },
  { value: "order_count", label: W.sortOrderCount }
];

const EMPTY_AGGREGATE: CustomerAggregateMetrics = {
  total_customers: 0,
  new_customers: 0,
  active_customers: 0,
  recurrent_customers: 0,
  vip_customers: 0,
  inactive_customers: 0,
  total_lifetime_value: "0",
  average_ticket: "0",
  average_orders_per_customer: "0"
};

export function Customer360Workspace() {
  const { accessToken, refreshSession } = useAuthStore();
  const [items, setItems] = useState<Customer360Summary[]>([]);
  const [aggregate, setAggregate] = useState<CustomerAggregateMetrics>(
    EMPTY_AGGREGATE
  );
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState<CrmStatusFilter>("all");
  const [isVipOnly, setIsVipOnly] = useState(false);
  const [isRecurrentOnly, setIsRecurrentOnly] = useState(false);
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [sortBy, setSortBy] = useState<CrmSortBy>("created_at");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");
  const [offset, setOffset] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const activeRef = useRef(true);
  const limit = 12;

  useEffect(() => {
    if (!accessToken) return;
    activeRef.current = true;
    loadData();
    return () => {
      activeRef.current = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    accessToken,
    search,
    status,
    isVipOnly,
    isRecurrentOnly,
    dateFrom,
    dateTo,
    sortBy,
    sortDir,
    offset
  ]);

  async function loadData(retried = false) {
    if (!accessToken) return;
    setIsLoading(true);
    setError(null);
    try {
      const [list, metrics] = await Promise.all([
        listCustomer360({
          accessToken,
          search: search || undefined,
          status,
          isVip: isVipOnly || undefined,
          isRecurrent: isRecurrentOnly || undefined,
          dateFrom: dateFrom || undefined,
          dateTo: dateTo || undefined,
          sortBy,
          sortDir,
          limit,
          offset
        }),
        getCustomerMetrics(accessToken).catch(() => null)
      ]);
      if (!activeRef.current) return;
      setItems(list.items);
      setTotal(list.total);
      if (list.aggregate) {
        setAggregate(list.aggregate);
      } else if (metrics) {
        setAggregate(metrics);
      }
    } catch (err) {
      if (!activeRef.current) return;
      if (!retried && err instanceof ApiError && err.status === 401) {
        try {
          await refreshSession();
        } catch {
          setError(W.errorLoad);
          return;
        }
        return loadData(true);
      }
      setError(W.errorLoad);
    } finally {
      if (activeRef.current) setIsLoading(false);
    }
  }

  const tableRows = useMemo(
    () =>
      items.map((customer) => ({
        customer: (
          <a
            href={`/dashboard/customers/${customer.id}`}
            className="flex items-center gap-3 text-left transition hover:opacity-80"
          >
            <Avatar name={customer.full_name} size="sm" />
            <span className="min-w-0 flex-1">
              <span className="block truncate font-medium text-foreground">
                {customer.full_name}
              </span>
              <span className="block truncate text-xs text-muted-foreground">
                {customer.email ??
                  customer.phone ??
                  customer.instagram_username ??
                  W.fallbackNotSet}
              </span>
            </span>
          </a>
        ),
        status: <CustomerLifecycleBadge status={customer.metrics.status} />,
        orders: (
          <span className="font-medium text-foreground">
            {formatNumber(customer.metrics.order_count)}
          </span>
        ),
        ltv: (
          <span className="font-semibold text-success">
            {formatCurrency(customer.metrics.lifetime_value)}
          </span>
        ),
        lastPurchase: (
          <span className="text-foreground">
            {customer.metrics.last_purchase_at
              ? formatDate(customer.metrics.last_purchase_at)
              : W.fallbackNotSet}
          </span>
        ),
        channel: (
          <span className="truncate text-foreground">
            {customer.whatsapp ||
              customer.instagram_username ||
              customer.phone ||
              W.fallbackNotSet}
          </span>
        )
      })),
    [items]
  );

  function clearFilters() {
    setSearch("");
    setStatus("all");
    setIsVipOnly(false);
    setIsRecurrentOnly(false);
    setDateFrom("");
    setDateTo("");
    setSortBy("created_at");
    setSortDir("desc");
    setOffset(0);
  }

  return (
    <div className="grid gap-6">
      <DashboardSection title="Métricas CRM">
        {isLoading && items.length === 0 ? (
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            {Array.from({ length: 8 }).map((_, i) => (
              <div
                key={i}
                className="rounded-xl border border-border bg-card p-5 shadow-xs"
              >
                <Skeleton className="h-4 w-24" />
                <Skeleton className="mt-5 h-8 w-32" />
              </div>
            ))}
          </div>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            <MetricCard
              title={M.totalCustomers}
              value={formatNumber(aggregate.total_customers)}
              icon={UsersRound}
              iconTone="primary"
            />
            <MetricCard
              title={M.newCustomers}
              value={formatNumber(aggregate.new_customers)}
              icon={UserPlus}
              iconTone="info"
            />
            <MetricCard
              title={M.activeCustomers}
              value={formatNumber(aggregate.active_customers)}
              icon={Sparkles}
              iconTone="success"
            />
            <MetricCard
              title={M.recurrentCustomers}
              value={formatNumber(aggregate.recurrent_customers)}
              icon={Filter}
              iconTone="purple"
            />
            <MetricCard
              title={M.vipCustomers}
              value={formatNumber(aggregate.vip_customers)}
              icon={Star}
              iconTone="warning"
            />
            <MetricCard
              title={M.inactiveCustomers}
              value={formatNumber(aggregate.inactive_customers)}
              icon={SlidersHorizontal}
              iconTone="destructive"
            />
            <MetricCard
              title={M.totalLifetimeValue}
              value={formatCurrency(aggregate.total_lifetime_value)}
              icon={Sparkles}
              iconTone="success"
            />
            <MetricCard
              title={M.averageTicket}
              value={formatCurrency(aggregate.average_ticket)}
              icon={Sparkles}
              iconTone="primary"
            />
          </div>
        )}
      </DashboardSection>

      <Card variant="elevated">
        <CardContent className="p-4">
          <div className="grid gap-3 lg:grid-cols-[minmax(0,1fr)_180px_180px_auto]">
            <div className="relative">
              <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <input
                className="h-10 w-full rounded-md border border-input bg-background pl-9 pr-3 text-sm shadow-xs outline-none focus-visible:ring-2 focus-visible:ring-ring"
                placeholder={W.searchPlaceholder}
                value={search}
                onChange={(event) => {
                  setSearch(event.target.value);
                  setOffset(0);
                }}
              />
            </div>
            <select
              className="h-10 rounded-md border border-input bg-background px-3 text-sm shadow-xs outline-none focus-visible:ring-2 focus-visible:ring-ring"
              value={status}
              onChange={(event) => {
                setStatus(event.target.value as CrmStatusFilter);
                setOffset(0);
              }}
            >
              {STATUS_FILTERS.map((s) => (
                <option key={s} value={s}>
                  {s === "all" ? W.allStatuses : t.crm.status[s]}
                </option>
              ))}
            </select>
            <select
              className="h-10 rounded-md border border-input bg-background px-3 text-sm shadow-xs outline-none focus-visible:ring-2 focus-visible:ring-ring"
              value={sortBy}
              onChange={(event) => {
                setSortBy(event.target.value as CrmSortBy);
                setOffset(0);
              }}
            >
              {SORT_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
            <Button
              type="button"
              variant="outline"
              onClick={() => {
                setSortDir((d) => (d === "asc" ? "desc" : "asc"));
              }}
            >
              {sortDir === "asc" ? "↑" : "↓"} {sortBy}
            </Button>
          </div>

          <div className="mt-3 grid gap-3 lg:grid-cols-[180px_180px_180px_180px_auto]">
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                className="h-4 w-4 rounded border-input"
                checked={isVipOnly}
                onChange={(event) => {
                  setIsVipOnly(event.target.checked);
                  setOffset(0);
                }}
              />
              <span className="inline-flex items-center gap-1">
                <Star className="h-3.5 w-3.5 text-amber-500" aria-hidden="true" />
                {W.filterVipOnly}
              </span>
            </label>
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                className="h-4 w-4 rounded border-input"
                checked={isRecurrentOnly}
                onChange={(event) => {
                  setIsRecurrentOnly(event.target.checked);
                  setOffset(0);
                }}
              />
              <span>{W.filterRecurrentOnly}</span>
            </label>
            <label className="grid gap-1 text-xs">
              <span className="text-muted-foreground">{W.dateFrom}</span>
              <input
                type="date"
                className="h-9 rounded-md border border-input bg-background px-2 text-sm"
                value={dateFrom}
                onChange={(event) => {
                  setDateFrom(event.target.value);
                  setOffset(0);
                }}
              />
            </label>
            <label className="grid gap-1 text-xs">
              <span className="text-muted-foreground">{W.dateTo}</span>
              <input
                type="date"
                className="h-9 rounded-md border border-input bg-background px-2 text-sm"
                value={dateTo}
                onChange={(event) => {
                  setDateTo(event.target.value);
                  setOffset(0);
                }}
              />
            </label>
            <Button type="button" variant="ghost" onClick={clearFilters}>
              {W.clearFilters}
            </Button>
          </div>
        </CardContent>
      </Card>

      {error ? (
        <div className="rounded-lg border border-destructive/25 bg-destructive/10 px-4 py-3 text-sm text-destructive">
          {error}
        </div>
      ) : null}

      <DashboardSection
        title={W.tableHeaderCustomer}
        description={
          total > 0
            ? W.paginationShowing
                .replace("{start}", String(offset + 1))
                .replace("{end}", String(offset + items.length))
                .replace("{total}", String(total))
            : W.paginationNone
        }
      >
        {isLoading && items.length === 0 ? (
          <div className="grid gap-3">
            {Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} className="h-16 w-full" />
            ))}
          </div>
        ) : items.length === 0 ? (
          <EmptyState
            icon={UsersRound}
            title={W.emptyTitle}
            description={W.emptyDesc}
          />
        ) : (
          <>
            <div className="hidden lg:block">
              <DataTable
                columns={[
                  { key: "customer", header: W.tableHeaderCustomer },
                  { key: "status", header: W.tableHeaderStatus },
                  { key: "orders", header: W.tableHeaderOrders },
                  { key: "ltv", header: W.tableHeaderLifetimeValue },
                  { key: "lastPurchase", header: W.tableHeaderLastPurchase },
                  { key: "channel", header: W.tableHeaderChannel }
                ]}
                rows={tableRows}
                isLoading={isLoading}
                emptyTitle={W.emptyTitle}
                emptyDescription={W.emptyDesc}
              />
            </div>
            <div className="grid gap-3 lg:hidden">
              {items.map((c) => (
                <a
                  key={c.id}
                  href={`/dashboard/customers/${c.id}`}
                  className="block rounded-lg border bg-card p-4 shadow-sm"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <p className="truncate font-medium">{c.full_name}</p>
                      <p className="mt-1 truncate text-xs text-muted-foreground">
                        {c.email ?? c.phone ?? c.instagram_username}
                      </p>
                    </div>
                    <CustomerLifecycleBadge status={c.metrics.status} />
                  </div>
                  <div className="mt-3 grid grid-cols-3 gap-2 text-xs">
                    <div>
                      <p className="text-muted-foreground">
                        {W.tableHeaderOrders}
                      </p>
                      <p className="mt-1 font-medium">
                        {formatNumber(c.metrics.order_count)}
                      </p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">
                        {W.tableHeaderLifetimeValue}
                      </p>
                      <p className="mt-1 font-medium">
                        {formatCurrency(c.metrics.lifetime_value)}
                      </p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">
                        {W.tableHeaderLastPurchase}
                      </p>
                      <p className="mt-1 font-medium">
                        {c.metrics.last_purchase_at
                          ? formatDate(c.metrics.last_purchase_at)
                          : "—"}
                      </p>
                    </div>
                  </div>
                </a>
              ))}
            </div>

            <div className="flex items-center justify-between pt-2 text-sm text-muted-foreground">
              <span>
                {W.paginationShowing
                  .replace("{start}", String(offset + 1))
                  .replace("{end}", String(offset + items.length))
                  .replace("{total}", String(total))}
              </span>
              <div className="flex gap-2">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  disabled={offset === 0}
                  onClick={() =>
                    setOffset((current) => Math.max(0, current - limit))
                  }
                >
                  {W.previous}
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  disabled={offset + limit >= total}
                  onClick={() => setOffset((current) => current + limit)}
                >
                  {W.next}
                </Button>
              </div>
            </div>
          </>
        )}
      </DashboardSection>
    </div>
  );
}
