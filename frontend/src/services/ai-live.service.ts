import { apiGet, apiPatch, apiPost } from "@/services/api-client";
import type {
  AIEventListResponse,
  AIStateResponse,
  ConversationInsightsResponse,
  HandoffResponse,
  IntentAnalysisResponse,
  SuggestReplyResponse,
} from "@/types/ai-live";

export function getAIState(accessToken: string, conversationId: string): Promise<AIStateResponse> {
  return apiGet<AIStateResponse>(`/ai-live/conversations/${conversationId}/state`, { accessToken });
}

export function getSuggestedReplies(
  accessToken: string,
  conversationId: string
): Promise<SuggestReplyResponse> {
  return apiPost<SuggestReplyResponse, Record<string, never>>(
    `/ai-live/conversations/${conversationId}/suggest-reply`,
    {},
    { accessToken }
  );
}

export function getInsights(
  accessToken: string,
  conversationId: string
): Promise<ConversationInsightsResponse> {
  return apiGet<ConversationInsightsResponse>(`/ai-live/conversations/${conversationId}/insights`, { accessToken });
}

export function toggleAI(
  accessToken: string,
  conversationId: string,
  aiEnabled: boolean
): Promise<AIStateResponse> {
  return apiPatch<AIStateResponse, { ai_enabled: boolean }>(
    `/ai-live/conversations/${conversationId}/toggle-ai`,
    { ai_enabled: aiEnabled },
    { accessToken }
  );
}

export function toggleAutoReply(
  accessToken: string,
  conversationId: string,
  autoReplyEnabled: boolean
): Promise<AIStateResponse> {
  return apiPatch<AIStateResponse, { auto_reply_enabled: boolean }>(
    `/ai-live/conversations/${conversationId}/toggle-auto-reply`,
    { auto_reply_enabled: autoReplyEnabled },
    { accessToken }
  );
}

export function requestHandoff(
  accessToken: string,
  conversationId: string
): Promise<HandoffResponse> {
  return apiPost<HandoffResponse, Record<string, never>>(
    `/ai-live/conversations/${conversationId}/handoff`,
    {},
    { accessToken }
  );
}

export function analyzeIntent(
  accessToken: string,
  conversationId: string,
  message: string
): Promise<IntentAnalysisResponse> {
  return apiPost<IntentAnalysisResponse, { message: string }>(
    `/ai-live/conversations/${conversationId}/analyze-intent`,
    { message },
    { accessToken }
  );
}

export function getAIEvents(
  accessToken: string,
  conversationId: string
): Promise<AIEventListResponse> {
  return apiGet<AIEventListResponse>(`/ai-live/conversations/${conversationId}/events`, { accessToken });
}
