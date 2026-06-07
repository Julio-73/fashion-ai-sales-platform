export type AutomationTaskStatus =
  | "pending"
  | "in_progress"
  | "completed"
  | "cancelled"
  | "overdue";

export type AutomationTaskPriority = "low" | "medium" | "high" | "critical";

export type AutomationTaskType =
  | "follow_up"
  | "call"
  | "proposal"
  | "meeting"
  | "recovery"
  | "alert"
  | "win_log"
  | "loss_log"
  | "pipeline_event"
  | "inventory_check"
  | "order_risk";

export type AutomationEventSeverity = "info" | "warning" | "critical";

export type AutomationEntityType =
  | "customer"
  | "pipeline_item"
  | "conversation"
  | "order"
  | "inventory_item"
  | "none";

export type AutomationRule = {
  id: string;
  empresa_id: string;
  rule_key: string;
  name: string;
  description: string | null;
  trigger_type: string;
  enabled: boolean;
  config: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export type AutomationTask = {
  id: string;
  empresa_id: string;
  rule_id: string | null;
  customer_id: string | null;
  pipeline_item_id: string | null;
  conversation_id: string | null;
  title: string;
  description: string | null;
  task_type: AutomationTaskType;
  priority: AutomationTaskPriority;
  status: AutomationTaskStatus;
  ai_reason: string | null;
  ai_next_action: string | null;
  ai_score: number | null;
  due_date: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
};

export type AutomationEvent = {
  id: string;
  empresa_id: string;
  rule_id: string | null;
  rule_key: string;
  event_type: string;
  entity_type: AutomationEntityType;
  entity_id: string | null;
  severity: AutomationEventSeverity;
  payload: Record<string, unknown>;
  created_at: string;
};

export type AutomationMetrics = {
  tasks_total: number;
  tasks_pending: number;
  tasks_today: number;
  tasks_this_week: number;
  tasks_overdue: number;
  tasks_completed: number;
  tasks_completion_rate_pct: number;
  alerts_total: number;
  alerts_critical: number;
  rules_enabled: number;
  rules_total: number;
  automation_executions: number;
  leads_recovered: number;
  won_after_automation: number;
  average_completion_hours: number;
  by_priority: Record<string, number>;
  by_task_type: Record<string, number>;
};

export type AutomationBoardColumn = {
  key: string;
  label: string;
  count: number;
  tasks: AutomationTask[];
};

export type AutomationTaskBoard = {
  columns: AutomationBoardColumn[];
  total: number;
};

export type AutomationCalendarEntry = {
  task_id: string;
  title: string;
  due_date: string;
  priority: AutomationTaskPriority;
  status: AutomationTaskStatus;
  task_type: AutomationTaskType;
  customer_id: string | null;
  pipeline_item_id: string | null;
};

export type AutomationCalendarView = {
  view: "day" | "week" | "month";
  range_start: string;
  range_end: string;
  entries: AutomationCalendarEntry[];
  total: number;
};

export type AutomationRunStats = {
  scanned_customers: number;
  scanned_deals: number;
  scanned_orders: number;
  scanned_inventory: number;
  tasks_created: number;
  tasks_updated: number;
  events_created: number;
  rules_skipped: string[];
};
