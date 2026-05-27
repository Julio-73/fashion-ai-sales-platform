import { AlertCircle, BrainCircuit, Gauge, Loader2, Thermometer, Zap } from "lucide-react";

import { Card } from "@/components/ui/card";
import type { AILiveState } from "@/types/ai-live";

type InsightsPanelProps = {
  state: AILiveState | null;
  isLoading: boolean;
  error: string | null;
};

function InsightRow({
  icon,
  label,
  value,
  color,
}: {
  icon: React.ReactNode;
  label: string;
  value: string | null;
  color?: string;
}) {
  return (
    <div className="flex items-center gap-2 rounded-md px-2 py-1.5 text-xs hover:bg-secondary">
      <span className="shrink-0 text-muted-foreground">{icon}</span>
      <span className="text-muted-foreground">{label}</span>
      <span className={`ml-auto font-medium ${color ?? ""}`}>
        {value ?? "—"}
      </span>
    </div>
  );
}

const intentLabels: Record<string, string> = {
  purchase_intent: "Purchase intent",
  pricing_intent: "Pricing inquiry",
  negotiation_intent: "Negotiation",
  shipping_intent: "Shipping inquiry",
  greeting: "Greeting",
  complaint: "Complaint",
  goodbye: "Goodbye",
  unknown: "Unknown",
};

const tempColors: Record<string, string> = {
  hot: "text-red-600",
  warm: "text-amber-600",
  cool: "text-blue-600",
  cold: "text-slate-500",
};

const sentimentColors: Record<string, string> = {
  positive: "text-emerald-600",
  neutral: "text-slate-500",
  negative: "text-red-600",
};

export function InsightsPanel({ state, isLoading, error }: InsightsPanelProps) {
  if (isLoading) {
    return (
      <Card className="p-3">
        <div className="flex items-center gap-2 text-xs font-medium text-muted-foreground mb-2">
          <Loader2 className="h-3 w-3 animate-spin" />
          Analyzing conversation...
        </div>
        <div className="space-y-2">
          <div className="h-7 animate-pulse rounded-md bg-muted" />
          <div className="h-7 animate-pulse rounded-md bg-muted" />
          <div className="h-7 animate-pulse rounded-md bg-muted" />
        </div>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="p-3">
        <div className="flex items-center gap-2 text-xs font-medium text-destructive mb-1">
          <AlertCircle className="h-3 w-3" />
          Analysis unavailable
        </div>
        <p className="text-[11px] text-muted-foreground">{error}</p>
      </Card>
    );
  }

  if (!state) {
    return null;
  }

  const intentLabel = state.last_detected_intent
    ? intentLabels[state.last_detected_intent] ?? state.last_detected_intent
    : null;
  const tempColor = state.lead_temperature ? tempColors[state.lead_temperature] : undefined;
  const sentColor = state.sentiment ? sentimentColors[state.sentiment] : undefined;

  return (
    <Card className="p-3">
      <div className="flex items-center gap-2 text-xs font-medium text-muted-foreground mb-2">
        <BrainCircuit className="h-3 w-3" />
        AI Insights
      </div>
      <div className="space-y-0.5">
        <InsightRow
          icon={<Zap className="h-3 w-3" />}
          label="Intent"
          value={intentLabel}
        />
        <InsightRow
          icon={<Gauge className="h-3 w-3" />}
          label="Sentiment"
          value={state.sentiment ? state.sentiment.charAt(0).toUpperCase() + state.sentiment.slice(1) : null}
          color={sentColor}
        />
        <InsightRow
          icon={<Gauge className="h-3 w-3" />}
          label="Urgency"
          value={state.urgency_score !== null ? state.urgency_score.toFixed(1) : null}
        />
        <InsightRow
          icon={<Thermometer className="h-3 w-3" />}
          label="Temperature"
          value={state.lead_temperature ? state.lead_temperature.charAt(0).toUpperCase() + state.lead_temperature.slice(1) : null}
          color={tempColor}
        />
        <InsightRow
          icon={<BrainCircuit className="h-3 w-3" />}
          label="Confidence"
          value={state.ai_confidence !== null ? `${(state.ai_confidence * 100).toFixed(0)}%` : null}
        />
      </div>
    </Card>
  );
}
