"use client";

import {
  AlertCircle,
  CheckCircle2,
  Crown,
  Flame,
  Mail,
  MessageCircle,
  Phone,
  Sparkles,
  TrendingUp,
  User,
  Webhook,
  type LucideIcon
} from "lucide-react";
import Link from "next/link";

import { Avatar } from "@/components/ui/avatar";
import { StatusPill } from "@/components/ui/status-pill";
import { formatCurrency } from "@/modules/crm/utils/format";
import { cn } from "@/lib/utils";
import type { PipelineItem } from "@/types/pipeline";

type Props = {
  deal: PipelineItem;
  isDragging?: boolean;
  onDragStart?: (e: React.DragEvent<HTMLDivElement>, deal: PipelineItem) => void;
  onDragEnd?: () => void;
};

const CHANNEL_ICON: Record<string, LucideIcon> = {
  whatsapp: MessageCircle,
  email: Mail,
  web: Webhook,
  phone: Phone,
  instagram: MessageCircle,
  manual: User
};

const CHANNEL_TONE: Record<string, "primary" | "success" | "warning" | "info" | "purple" | "neutral"> = {
  whatsapp: "success",
  email: "info",
  web: "purple",
  phone: "warning",
  instagram: "primary",
  manual: "neutral"
};

const CHANNEL_LABEL: Record<string, string> = {
  whatsapp: "WhatsApp",
  email: "Email",
  web: "Web",
  phone: "Teléfono",
  instagram: "Instagram",
  manual: "Manual"
};

function daysSince(iso: string | null | undefined): number {
  if (!iso) return 0;
  const d = new Date(iso).getTime();
  if (Number.isNaN(d)) return 0;
  return Math.max(0, Math.floor((Date.now() - d) / 86_400_000));
}

export function LeadCard({
  deal,
  isDragging = false,
  onDragStart,
  onDragEnd
}: Props) {
  const channel = deal.channel ?? "manual";
  const ChannelIcon = CHANNEL_ICON[channel] ?? User;
  const tone = CHANNEL_TONE[channel] ?? "neutral";
  const score = deal.ai_score?.total ?? null;
  const customerName = deal.customer?.full_name ?? "Sin cliente";
  const daysInStage = daysSince(deal.stage_entered_at);
  const priority = deal.customer?.priority ?? "cold";
  const leadScore = deal.customer?.lead_score ?? 0;
  const ordersCount = deal.customer?.orders_count ?? 0;
  const ltv = deal.customer?.lifetime_value ?? 0;
  const isHot = priority === "hot" || leadScore >= 80;
  const isStuck = daysInStage >= 7;

  return (
    <div
      draggable
      onDragStart={(e) => onDragStart?.(e, deal)}
      onDragEnd={onDragEnd}
      className={cn(
        "group cursor-grab overflow-hidden rounded-xl border bg-card p-3 shadow-xs transition-all",
        "hover:-translate-y-px hover:border-primary-200 hover:shadow-md",
        isDragging && "opacity-50 ring-2 ring-primary",
        isStuck && "ring-1 ring-warning-200"
      )}
      data-testid={`lead-card-${deal.id}`}
    >
      <div className="flex items-start justify-between gap-2">
        <Link
          href={`/dashboard/pipeline/${deal.id}`}
          className="line-clamp-2 text-sm font-semibold tracking-tight text-foreground transition-colors hover:text-primary"
        >
          {deal.title}
        </Link>
        {deal.is_vip ? (
          <span
            className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300"
            aria-label="VIP"
            title="Cliente VIP"
          >
            <Crown className="h-3 w-3" />
          </span>
        ) : null}
      </div>

      <div className="mt-2 flex items-center gap-1.5">
        <Avatar name={customerName} size="xs" />
        <span className="truncate text-xs text-muted-foreground">
          {customerName}
        </span>
        {ordersCount > 0 ? (
          <span className="ml-auto inline-flex items-center gap-0.5 text-[10px] font-medium text-success">
            <CheckCircle2 className="h-3 w-3" />
            {ordersCount}
          </span>
        ) : null}
      </div>

      <div className="mt-3 flex items-end justify-between">
        <div>
          <div className="text-base font-semibold tracking-tight text-foreground">
            {formatCurrency(deal.estimated_value)}
          </div>
          <div className="text-[10px] uppercase tracking-wider text-muted-foreground">
            {deal.probability}% prob.
          </div>
        </div>
        {score !== null ? (
          <div className="flex flex-col items-end">
            <StatusPill
              tone={
                score >= 75 ? "success" : score >= 45 ? "warning" : "neutral"
              }
              size="sm"
              icon={<Sparkles className="h-3 w-3" />}
            >
              {score}
            </StatusPill>
            <span className="mt-0.5 text-[10px] text-muted-foreground">
              AI score
            </span>
          </div>
        ) : null}
      </div>

      <div className="mt-3 h-1 w-full overflow-hidden rounded-full bg-muted">
        <div
          className="h-full rounded-full bg-gradient-to-r from-primary to-purple transition-all"
          style={{ width: `${Math.max(2, deal.probability)}%` }}
        />
      </div>

      <div className="mt-2.5 flex items-center justify-between gap-1.5">
        <StatusPill tone={tone} size="sm">
          <ChannelIcon className="h-3 w-3" aria-hidden="true" />
          {CHANNEL_LABEL[channel]}
        </StatusPill>
        <div className="flex items-center gap-1.5 text-[10px] text-muted-foreground">
          <span className="inline-flex items-center gap-0.5">
            <TrendingUp className="h-3 w-3" aria-hidden="true" />
            {daysInStage}d
          </span>
          {isHot ? (
            <Flame
              className="h-3 w-3 text-orange-500"
              aria-label="Lead caliente"
            />
          ) : null}
          {ltv > 0 ? (
            <span className="font-semibold text-success">
              LTV {formatCurrency(ltv)}
            </span>
          ) : null}
        </div>
      </div>

      {isStuck ? (
        <div className="mt-2 flex items-center gap-1 rounded-md bg-warning-50 px-2 py-1 text-[10px] font-medium text-warning ring-1 ring-inset ring-warning-200 dark:bg-warning-50/20 dark:text-warning-200 dark:ring-warning-200/30">
          <AlertCircle className="h-3 w-3" aria-hidden="true" />
          Estancado hace {daysInStage}d
        </div>
      ) : null}
    </div>
  );
}
