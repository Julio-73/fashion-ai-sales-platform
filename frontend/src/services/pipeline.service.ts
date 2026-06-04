import { apiDelete, apiGet, apiPatch, apiPost } from "@/services/api-client";
import type {
  PipelineAIScore,
  PipelineAlerts,
  PipelineBoard,
  PipelineDashboard,
  PipelineFunnel,
  PipelineItem,
  PipelineItemCreate,
  PipelineItemMoveStage,
  PipelineItemUpdate,
  PipelineMetrics,
  PipelineRecommendations,
  PipelineStageInfo
} from "@/types/pipeline";

const STAGES_PATH = "/pipeline/stages";
const BOARD_PATH = "/pipeline/board";
const METRICS_PATH = "/pipeline/metrics";
const FUNNEL_PATH = "/pipeline/funnel";
const ALERTS_PATH = "/pipeline/alerts";
const RECOMMENDATIONS_PATH = "/pipeline/recommendations";
const DASHBOARD_PATH = "/pipeline/dashboard";
const DEALS_PATH = "/pipeline/deals";

export async function fetchStages(
  accessToken: string
): Promise<PipelineStageInfo[]> {
  return apiGet<PipelineStageInfo[]>(STAGES_PATH, { accessToken });
}

export async function fetchBoard(
  accessToken: string,
  filters: { stage?: string; is_open?: boolean; search?: string } = {}
): Promise<PipelineBoard> {
  const params = new URLSearchParams();
  if (filters.stage) params.set("stage", filters.stage);
  if (typeof filters.is_open === "boolean") {
    params.set("is_open", String(filters.is_open));
  }
  if (filters.search) params.set("search", filters.search);
  const qs = params.toString();
  return apiGet<PipelineBoard>(`${BOARD_PATH}${qs ? `?${qs}` : ""}`, {
    accessToken
  });
}

export async function fetchMetrics(
  accessToken: string
): Promise<PipelineMetrics> {
  return apiGet<PipelineMetrics>(METRICS_PATH, { accessToken });
}

export async function fetchFunnel(
  accessToken: string
): Promise<PipelineFunnel> {
  return apiGet<PipelineFunnel>(FUNNEL_PATH, { accessToken });
}

export async function fetchAlerts(
  accessToken: string
): Promise<PipelineAlerts> {
  return apiGet<PipelineAlerts>(ALERTS_PATH, { accessToken });
}

export async function fetchRecommendations(
  accessToken: string
): Promise<PipelineRecommendations> {
  return apiGet<PipelineRecommendations>(RECOMMENDATIONS_PATH, { accessToken });
}

export async function fetchDashboard(
  accessToken: string
): Promise<PipelineDashboard> {
  return apiGet<PipelineDashboard>(DASHBOARD_PATH, { accessToken });
}

export async function createDeal(
  accessToken: string,
  payload: PipelineItemCreate
): Promise<PipelineItem> {
  return apiPost<PipelineItem, PipelineItemCreate>(DEALS_PATH, payload, {
    accessToken
  });
}

export async function getDeal(
  accessToken: string,
  dealId: string
): Promise<PipelineItem> {
  return apiGet<PipelineItem>(`${DEALS_PATH}/${dealId}`, { accessToken });
}

export async function updateDeal(
  accessToken: string,
  dealId: string,
  payload: PipelineItemUpdate
): Promise<PipelineItem> {
  return apiPatch<PipelineItem, PipelineItemUpdate>(
    `${DEALS_PATH}/${dealId}`,
    payload,
    { accessToken }
  );
}

export async function moveDealStage(
  accessToken: string,
  dealId: string,
  payload: PipelineItemMoveStage
): Promise<PipelineItem> {
  return apiPost<PipelineItem, PipelineItemMoveStage>(
    `${DEALS_PATH}/${dealId}/move-stage`,
    payload,
    { accessToken }
  );
}

export async function deleteDeal(
  accessToken: string,
  dealId: string
): Promise<void> {
  await apiDelete(`${DEALS_PATH}/${dealId}`, { accessToken });
}

export async function scoreDeal(
  accessToken: string,
  dealId: string
): Promise<PipelineAIScore> {
  return apiPost<PipelineAIScore, Record<string, never>>(
    `${DEALS_PATH}/${dealId}/ai-score`,
    {},
    { accessToken }
  );
}
