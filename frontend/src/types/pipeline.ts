export type PipelineStageKey =
  | "new_lead"
  | "contacted"
  | "qualified"
  | "proposal"
  | "negotiation"
  | "won"
  | "lost";

export const PIPELINE_STAGE_KEYS: PipelineStageKey[] = [
  "new_lead",
  "contacted",
  "qualified",
  "proposal",
  "negotiation",
  "won",
  "lost",
];

export type PipelineChannel =
  | "whatsapp"
  | "email"
  | "web"
  | "phone"
  | "instagram"
  | "manual"
  | string;

export type PipelinePriority = "cold" | "warm" | "hot" | string;

export type AlertSeverity = "info" | "warning" | "critical";

export type AlertRule =
  | "STUCK_IN_STAGE"
  | "COLD_LEAD"
  | "VIP_IGNORED"
  | "HIGH_INTENT_SILENT"
  | "NEAR_BUDGET_OVERFLOW"
  | "NO_ACTIVITY_48H"
  | "NEGOTIATION_STUCK_7D"
  | "WON_DEAL"
  | "LOST_DEAL";

export type PipelineStageInfo = {
  key: PipelineStageKey;
  label: string;
  description: string;
  is_open: boolean;
  is_terminal: boolean;
  order: number;
  default_probability: number;
  color: string;
};

export type CustomerSummary = {
  id: string;
  full_name: string;
  email: string | null;
  phone: string | null;
  whatsapp: string | null;
  lead_status: string | null;
  priority: PipelinePriority | null;
  lead_score: number;
  is_vip: boolean;
  last_interaction_at: string | null;
  conversation_count: number;
  lifetime_value: number;
  orders_count: number;
};

export type AIScoreBreakdown = {
  total: number;
  intent: number;
  engagement: number;
  recency: number;
  monetary: number;
  sentiment: number;
  rationale: string[];
};

export type PipelineItem = {
  id: string;
  empresa_id: string;
  customer_id: string | null;
  conversation_id: string | null;
  order_id: string | null;
  title: string;
  estimated_value: number;
  probability: number;
  stage: PipelineStageKey;
  stage_entered_at: string;
  last_activity_at: string;
  notes: string | null;
  won_reason: string | null;
  lost_reason: string | null;
  position: number;
  channel: PipelineChannel | null;
  is_vip: boolean;
  created_at: string;
  updated_at: string;
  customer: CustomerSummary | null;
  ai_score: AIScoreBreakdown | null;
};

export type PipelineBoard = {
  items: PipelineItem[];
  total: number;
  by_stage: Record<string, number>;
  value_by_stage: Record<string, number>;
};

export type PipelineStageBreakdown = {
  count: number;
  value: number;
  average_value: number;
};

export type PipelineChannelBreakdown = {
  count: number;
  value: number;
};

export type PipelinePriorityBreakdown = {
  count: number;
};

export type PipelineMetrics = {
  total_open: number;
  total_closed_won: number;
  total_closed_lost: number;
  new_leads: number;
  open_value: number;
  weighted_open_value: number;
  won_value: number;
  lost_value: number;
  conversion_rate_pct: number;
  average_deal_value: number;
  average_time_to_close_days: number;
  average_time_in_current_stage_days: number;
  oldest_unstuck_days: number;
  alerts_count: number;
  by_stage: Record<string, PipelineStageBreakdown>;
  by_channel: Record<string, PipelineChannelBreakdown>;
  by_priority: Record<string, PipelinePriorityBreakdown>;
};

export type PipelineFunnelStage = {
  key: PipelineStageKey;
  label: string;
  color: string;
  count: number;
  value: number;
};

export type PipelineFunnel = {
  stages: PipelineFunnelStage[];
  total_open: number;
  total_closed: number;
  won_value: number;
  lost_value: number;
};

export type PipelineAlert = {
  id: string;
  deal_id: string;
  deal_title: string;
  customer_id: string | null;
  rule: AlertRule;
  severity: AlertSeverity;
  message: string;
  suggested_action: string;
  stage: PipelineStageKey;
  days_in_stage: number;
  created_at: string;
};

export type PipelineAlerts = {
  alerts: PipelineAlert[];
  total: number;
};

export type PipelineRecommendation = {
  deal_id: string;
  score: number;
  breakdown: AIScoreBreakdown;
  next_best_action: string;
  suggested_channel: PipelineChannel | null;
  suggested_stage: PipelineStageKey | null;
  notes: string[];
};

export type PipelineRecommendations = {
  recommendations: PipelineRecommendation[];
  total: number;
};

export type PipelineAIScore = {
  deal_id: string;
  score: number;
  breakdown: AIScoreBreakdown;
};

export type PipelineDashboard = {
  metrics: PipelineMetrics;
  funnel: PipelineFunnel;
  alerts: PipelineAlerts;
  top_deals: PipelineItem[];
  generated_at: string;
};

export type PipelineItemCreate = {
  title: string;
  estimated_value?: number;
  probability?: number;
  stage?: PipelineStageKey;
  notes?: string;
  channel?: PipelineChannel;
  is_vip?: boolean;
  customer_id?: string;
  conversation_id?: string;
  order_id?: string;
};

export type PipelineItemUpdate = {
  title?: string;
  estimated_value?: number;
  probability?: number;
  notes?: string;
  channel?: PipelineChannel;
  is_vip?: boolean;
  customer_id?: string;
  conversation_id?: string;
  order_id?: string;
};

export type PipelineItemMoveStage = {
  target_stage: PipelineStageKey;
  probability?: number;
  notes?: string;
  won_reason?: string;
  lost_reason?: string;
};
