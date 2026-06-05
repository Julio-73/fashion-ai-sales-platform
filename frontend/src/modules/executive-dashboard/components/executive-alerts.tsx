"use client";

import {
  AlertCircle,
  AlertTriangle,
  CheckCircle2,
  Clock,
  MessageCircle,
  Package,
  ShoppingCart,
  Users
} from "lucide-react";
import Link from "next/link";
import type { LucideIcon } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import type { ExecutiveDashboardAlerts } from "@/types/executive-dashboard";
import { cn } from "@/lib/utils";

type ExecutiveAlertsProps = {
  alerts: ExecutiveDashboardAlerts | null;
  isLoading: boolean;
};

const currencyFormatter = new Intl.NumberFormat("es-PE", {
  style: "currency",
  currency: "PEN",
  maximumFractionDigits: 0,
});

const numberFormatter = new Intl.NumberFormat("es-PE");

type AlertSection = {
  key: keyof ExecutiveDashboardAlerts;
  title: string;
  icon: LucideIcon;
  count: number;
  render: () => React.ReactNode;
  href?: string;
};

function shortDate(iso: string | null) {
  if (!iso) return "—";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "—";
  return d.toLocaleDateString("es-PE", { day: "2-digit", month: "short" });
}

function formatHours(hours: number) {
  if (hours < 1) return "Menos de 1h";
  if (hours < 24) return `${Math.round(hours)}h`;
  return `${Math.floor(hours / 24)}d ${Math.round(hours % 24)}h`;
}

export function ExecutiveAlerts({ alerts, isLoading }: ExecutiveAlertsProps) {
  const sections: AlertSection[] = [
    {
      key: "inventory_critical",
      title: "Inventario crítico",
      icon: Package,
      count: alerts?.inventory_critical.length ?? 0,
      render: () => (
        <ul className="space-y-2">
          {(alerts?.inventory_critical ?? []).slice(0, 5).map((item) => (
            <li
              key={item.product_id}
              className="flex items-center justify-between gap-2 rounded-md border bg-card px-3 py-2"
            >
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium text-foreground">{item.name}</p>
                <p className="text-[11px] text-muted-foreground">
                  Stock {item.stock} · mínimo {item.min_stock}
                </p>
              </div>
              <span className="rounded-md bg-rose-50 px-2 py-0.5 text-[11px] font-semibold text-rose-700">
                {item.status}
              </span>
            </li>
          ))}
        </ul>
      ),
      href: "/dashboard/inventory",
    },
    {
      key: "leads_abandoned",
      title: "Leads abandonados",
      icon: AlertTriangle,
      count: alerts?.leads_abandoned.length ?? 0,
      render: () => (
        <ul className="space-y-2">
          {(alerts?.leads_abandoned ?? []).slice(0, 5).map((deal) => (
            <li
              key={deal.deal_id}
              className="flex items-center justify-between gap-2 rounded-md border bg-card px-3 py-2"
            >
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium text-foreground">{deal.title}</p>
                <p className="text-[11px] text-muted-foreground">
                  {deal.stage} · {deal.days_inactive} días sin actividad
                </p>
              </div>
              <span className="rounded-md bg-amber-50 px-2 py-0.5 text-[11px] font-mono font-semibold text-amber-700">
                {currencyFormatter.format(deal.value)}
              </span>
            </li>
          ))}
        </ul>
      ),
      href: "/dashboard/pipeline",
    },
    {
      key: "conversations_unanswered",
      title: "Conversaciones sin respuesta",
      icon: MessageCircle,
      count: alerts?.conversations_unanswered.length ?? 0,
      render: () => (
        <ul className="space-y-2">
          {(alerts?.conversations_unanswered ?? []).slice(0, 5).map((item) => (
            <li
              key={item.conversation_id}
              className="flex items-center justify-between gap-2 rounded-md border bg-card px-3 py-2"
            >
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium text-foreground">
                  {item.customer_name ?? "Cliente sin nombre"}
                </p>
                <p className="text-[11px] text-muted-foreground">
                  {item.channel} · {shortDate(item.last_message_at)}
                </p>
              </div>
              <span className="inline-flex items-center gap-1 rounded-md bg-amber-50 px-2 py-0.5 text-[11px] font-semibold text-amber-700">
                <Clock className="h-3 w-3" />
                {formatHours(item.hours_silent)}
              </span>
            </li>
          ))}
        </ul>
      ),
      href: "/dashboard/conversations",
    },
    {
      key: "inactive_customers",
      title: "Clientes inactivos",
      icon: Users,
      count: alerts?.inactive_customers.length ?? 0,
      render: () => (
        <ul className="space-y-2">
          {(alerts?.inactive_customers ?? []).slice(0, 5).map((item) => (
            <li
              key={item.customer_id}
              className="flex items-center justify-between gap-2 rounded-md border bg-card px-3 py-2"
            >
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium text-foreground">{item.full_name}</p>
                <p className="text-[11px] text-muted-foreground">
                  Última compra: {shortDate(item.last_purchase_at)}
                </p>
              </div>
              <span className="rounded-md bg-slate-100 px-2 py-0.5 text-[11px] font-semibold text-slate-600">
                {item.days_inactive} días
              </span>
            </li>
          ))}
        </ul>
      ),
      href: "/dashboard/customers",
    },
    {
      key: "delayed_orders",
      title: "Pedidos retrasados",
      icon: ShoppingCart,
      count: alerts?.delayed_orders.length ?? 0,
      render: () => (
        <ul className="space-y-2">
          {(alerts?.delayed_orders ?? []).slice(0, 5).map((order) => (
            <li
              key={order.order_id}
              className="flex items-center justify-between gap-2 rounded-md border bg-card px-3 py-2"
            >
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium text-foreground">
                  {order.order_number} · {order.customer_name}
                </p>
                <p className="text-[11px] text-muted-foreground">
                  {order.status} · {order.days_since_created} días
                </p>
              </div>
              <span className="rounded-md bg-rose-50 px-2 py-0.5 text-[11px] font-mono font-semibold text-rose-700">
                {currencyFormatter.format(order.total)}
              </span>
            </li>
          ))}
        </ul>
      ),
      href: "/dashboard/orders",
    },
  ];

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Alertas críticas</CardTitle>
          <p className="text-xs text-muted-foreground">
            Incidencias operativas que requieren atención inmediata.
          </p>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {Array.from({ length: 5 }).map((_, i) => (
              <Skeleton key={i} className="h-40" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  const visible = sections.filter((section) => section.count > 0);

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-rose-50 text-rose-700">
            <AlertCircle className="h-4 w-4" />
          </div>
          <div>
            <CardTitle className="text-sm">Alertas críticas</CardTitle>
            <p className="text-xs text-muted-foreground">
              Incidencias operativas que requieren atención inmediata.
            </p>
          </div>
          <span className="ml-auto rounded-full bg-rose-50 px-2 py-0.5 text-xs font-medium text-rose-700">
            {visible.reduce((acc, section) => acc + section.count, 0)} totales
          </span>
        </div>
      </CardHeader>
      <CardContent>
        {visible.length === 0 ? (
          <div className="flex flex-col items-center gap-2 py-6 text-center">
            <CheckCircle2 className="h-8 w-8 text-emerald-500" />
            <p className="text-sm font-medium text-foreground">Todo en orden</p>
            <p className="text-xs text-muted-foreground">
              No hay alertas críticas activas en este momento.
            </p>
          </div>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {visible.map((section) => {
              const Icon = section.icon;
              return (
                <div
                  key={section.key}
                  className="flex flex-col gap-3 rounded-lg border bg-background p-4"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className="flex h-7 w-7 items-center justify-center rounded-md bg-rose-50 text-rose-700">
                        <Icon className="h-3.5 w-3.5" />
                      </div>
                      <p className="text-sm font-semibold text-foreground">{section.title}</p>
                    </div>
                    <span
                      className={cn(
                        "rounded-md px-2 py-0.5 text-[11px] font-semibold",
                        section.count > 0
                          ? "bg-rose-50 text-rose-700"
                          : "bg-emerald-50 text-emerald-700"
                      )}
                    >
                      {numberFormatter.format(section.count)}
                    </span>
                  </div>
                  {section.render()}
                  {section.href ? (
                    <Link
                      href={section.href}
                      className="mt-auto text-[11px] font-medium text-primary hover:underline"
                    >
                      Ver detalle →
                    </Link>
                  ) : null}
                </div>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
