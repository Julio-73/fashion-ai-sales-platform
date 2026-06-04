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
  Webhook
} from "lucide-react";
import Link from "next/link";

import { formatCurrency } from "@/modules/crm/utils/format";
import type { PipelineItem } from "@/types/pipeline";

type Props = {
  deal: PipelineItem;
  isDragging?: boolean;
  onDragStart?: (e: React.DragEvent<HTMLDivElement>, deal: PipelineItem) => void;
  onDragEnd?: () => void;
};

const CHANNEL_ICON: Record<string, typeof MessageCircle> = {
  whatsapp: MessageCircle,
  email: Mail,
  web: Webhook,
  phone: Phone,
  instagram: MessageCircle,
  manual: User
};

const CHANNEL_COLOR: Record<string, string> = {
  whatsapp: "text-emerald-600",
  email: "text-blue-600",
  web: "text-violet-600",
  phone: "text-amber-600",
  instagram: "text-pink-600",
  manual: "text-slate-600"
};

function daysSince(iso: string | null | undefined): number {
  if (!iso) return 0;
  const d = new Date(iso).getTime();
  if (Number.isNaN(d)) return 0;
  return Math.max(0, Math.floor((Date.now() - d) / 86_400_000));
}

export function LeadCard({ deal, isDragging = false, onDragStart, onDragEnd }: Props) {
  const channel = deal.channel ?? "manual";
  const ChannelIcon = CHANNEL_ICON[channel] ?? User;
  const channelColor = CHANNEL_COLOR[channel] ?? "text-slate-500";
  const score = deal.ai_score?.total ?? null;
  const customerName = deal.customer?.full_name ?? "Sin cliente";
  const daysInStage = daysSince(deal.stage_entered_at);
  const priority = deal.customer?.priority ?? "cold";
  const leadScore = deal.customer?.lead_score ?? 0;
  const ordersCount = deal.customer?.orders_count ?? 0;
  const ltv = deal.customer?.lifetime_value ?? 0;

  return (
    <div
      draggable
      onDragStart={(e) => onDragStart?.(e, deal)}
      onDragEnd={onDragEnd}
      className={`group cursor-grab rounded-lg border border-slate-200 bg-white p-3 shadow-sm transition hover:border-indigo-300 hover:shadow-md ${
        isDragging ? "opacity-50" : ""
      }`}
      data-testid={`lead-card-${deal.id}`}
    >
      <div className="flex items-start justify-between gap-2">
        <Link
          href={`/dashboard/pipeline/${deal.id}`}
          className="line-clamp-2 text-sm font-semibold text-slate-900 hover:text-indigo-600"
        >
          {deal.title}
        </Link>
        {deal.is_vip ? (
          <Crown
            className="h-4 w-4 flex-shrink-0 text-amber-500"
            aria-label="VIP"
          />
        ) : null}
      </div>

      <div className="mt-1.5 flex items-center gap-1.5 text-xs text-slate-500">
        <ChannelIcon className={`h-3.5 w-3.5 ${channelColor}`} />
        <span className="truncate">{customerName}</span>
        {ordersCount > 0 ? (
          <span className="ml-auto flex items-center gap-0.5 text-[10px] text-emerald-600">
            <CheckCircle2 className="h-3 w-3" />
            {ordersCount}
          </span>
        ) : null}
      </div>

      <div className="mt-3 flex items-center justify-between">
        <div>
          <div className="text-base font-bold text-slate-900">
            {formatCurrency(deal.estimated_value)}
          </div>
          <div className="text-[10px] uppercase tracking-wide text-slate-400">
            {deal.probability}% prob.
          </div>
        </div>
        {score !== null ? (
          <div className="flex flex-col items-end">
            <div
              className={`flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-semibold ${
                score >= 75
                  ? "bg-emerald-50 text-emerald-700"
                  : score >= 45
                  ? "bg-amber-50 text-amber-700"
                  : "bg-slate-100 text-slate-700"
              }`}
              title="AI score"
            >
              <Sparkles className="h-3 w-3" />
              {score}
            </div>
            <div className="mt-0.5 text-[10px] text-slate-400">AI score</div>
          </div>
        ) : null}
      </div>

      <div className="mt-3 h-1 w-full overflow-hidden rounded-full bg-slate-100">
        <div
          className="h-full rounded-full bg-indigo-500"
          style={{ width: `${Math.max(2, deal.probability)}%` }}
        />
      </div>

      <div className="mt-2.5 flex items-center justify-between text-[10px] text-slate-500">
        <span className="flex items-center gap-1">
          <TrendingUp className="h-3 w-3" />
          {daysInStage}d en etapa
        </span>
        <div className="flex items-center gap-1">
          {priority === "hot" || leadScore >= 80 ? (
            <Flame className="h-3 w-3 text-orange-500" />
          ) : null}
          {ltv > 0 ? (
            <span className="font-medium text-emerald-600">
              LTV {formatCurrency(ltv)}
            </span>
          ) : null}
        </div>
      </div>

      {daysInStage >= 7 ? (
        <div className="mt-2 flex items-center gap-1 rounded bg-amber-50 px-2 py-1 text-[10px] font-medium text-amber-700">
          <AlertCircle className="h-3 w-3" />
          Estancado hace {daysInStage}d
        </div>
      ) : null}
    </div>
  );
}
