import {
  apiGet,
  apiPatch,
  apiPost
} from "@/services/api-client";
import type {
  AutomationCalendarView,
  AutomationEvent,
  AutomationMetrics,
  AutomationRule,
  AutomationRunStats,
  AutomationTask,
  AutomationTaskBoard
} from "@/types/automation";

const RULES_PATH = "/automation/rules";
const TASKS_PATH = "/automation/tasks";
const BOARD_PATH = "/automation/tasks/board";
const EVENTS_PATH = "/automation/events";
const METRICS_PATH = "/automation/metrics";
const CALENDAR_PATH = "/automation/calendar";
const RUN_PATH = "/automation/run";

export async function fetchRules(
  accessToken: string,
  options: { enabled?: boolean } = {}
): Promise<AutomationRule[]> {
  const qs =
    typeof options.enabled === "boolean"
      ? `?enabled=${options.enabled ? "true" : "false"}`
      : "";
  return apiGet<AutomationRule[]>(`${RULES_PATH}${qs}`, { accessToken });
}

export async function seedRules(accessToken: string): Promise<AutomationRule[]> {
  return apiPost<AutomationRule[], Record<string, never>>(
    RULES_PATH + "/seed",
    {},
    { accessToken }
  );
}

export async function toggleRule(
  accessToken: string,
  ruleId: string,
  enabled: boolean
): Promise<AutomationRule> {
  return apiPatch<AutomationRule, { enabled: boolean }>(
    `${RULES_PATH}/${ruleId}`,
    { enabled },
    { accessToken }
  );
}

export async function runEngine(accessToken: string): Promise<AutomationRunStats> {
  return apiPost<AutomationRunStats, Record<string, never>>(
    RUN_PATH,
    {},
    { accessToken }
  );
}

export async function fetchTasks(
  accessToken: string,
  filters: {
    status?: string;
    priority?: string;
    task_type?: string;
    customer_id?: string;
    pipeline_item_id?: string;
    rule_id?: string;
    search?: string;
  } = {}
): Promise<AutomationTask[]> {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([k, v]) => {
    if (v) params.set(k, String(v));
  });
  const qs = params.toString();
  return apiGet<AutomationTask[]>(`${TASKS_PATH}${qs ? `?${qs}` : ""}`, {
    accessToken
  });
}

export async function fetchTaskBoard(
  accessToken: string
): Promise<AutomationTaskBoard> {
  return apiGet<AutomationTaskBoard>(BOARD_PATH, { accessToken });
}

export async function completeTask(
  accessToken: string,
  taskId: string
): Promise<AutomationTask> {
  return apiPost<AutomationTask, Record<string, never>>(
    `${TASKS_PATH}/${taskId}/complete`,
    {},
    { accessToken }
  );
}

export async function cancelTask(
  accessToken: string,
  taskId: string
): Promise<AutomationTask> {
  return apiPost<AutomationTask, Record<string, never>>(
    `${TASKS_PATH}/${taskId}/cancel`,
    {},
    { accessToken }
  );
}

export async function updateTask(
  accessToken: string,
  taskId: string,
  payload: Partial<AutomationTask>
): Promise<AutomationTask> {
  return apiPatch<AutomationTask, Partial<AutomationTask>>(
    `${TASKS_PATH}/${taskId}`,
    payload,
    { accessToken }
  );
}

export async function fetchEvents(
  accessToken: string,
  options: {
    rule_key?: string;
    entity_type?: string;
    severity?: string;
    limit?: number;
  } = {}
): Promise<AutomationEvent[]> {
  const params = new URLSearchParams();
  if (options.rule_key) params.set("rule_key", options.rule_key);
  if (options.entity_type) params.set("entity_type", options.entity_type);
  if (options.severity) params.set("severity", options.severity);
  if (options.limit) params.set("limit", String(options.limit));
  const qs = params.toString();
  return apiGet<AutomationEvent[]>(`${EVENTS_PATH}${qs ? `?${qs}` : ""}`, {
    accessToken
  });
}

export async function fetchMetrics(
  accessToken: string
): Promise<AutomationMetrics> {
  return apiGet<AutomationMetrics>(METRICS_PATH, { accessToken });
}

export async function fetchCalendar(
  accessToken: string,
  options: { view?: "day" | "week" | "month"; anchor?: string } = {}
): Promise<AutomationCalendarView> {
  const params = new URLSearchParams();
  if (options.view) params.set("view", options.view);
  if (options.anchor) params.set("anchor", options.anchor);
  const qs = params.toString();
  return apiGet<AutomationCalendarView>(`${CALENDAR_PATH}${qs ? `?${qs}` : ""}`, {
    accessToken
  });
}
