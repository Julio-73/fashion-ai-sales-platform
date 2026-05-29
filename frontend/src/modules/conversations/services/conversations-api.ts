import { apiDelete, apiGet, apiPatch, apiPost } from "@/services/api-client";
import type {
  AddMessageCoreResponse,
  ConversationCreatePayload,
  ConversationDetail,
  ConversationListResponse,
  ConversationSummary,
  ConversationUpdatePayload,
  ConversationStatus,
  MessageCreatePayload,
  MessageSummary,
  ProcessMessagePayload,
  ProcessMessageResponse,
  TypingState,
} from "@/types/conversation";

type ListConversationsParams = {
  accessToken: string;
  search?: string;
  estado?: ConversationStatus | "all";
  limit?: number;
  offset?: number;
};

function buildConversationQuery(params: ListConversationsParams) {
  const query = new URLSearchParams();
  query.set("limit", String(params.limit ?? 25));
  query.set("offset", String(params.offset ?? 0));
  if (params.search) query.set("search", params.search);
  if (params.estado && params.estado !== "all") query.set("estado", params.estado);
  return query.toString();
}

export function listConversations(params: ListConversationsParams): Promise<ConversationListResponse> {
  return apiGet<ConversationListResponse>(`/conversations?${buildConversationQuery(params)}`, {
    accessToken: params.accessToken,
  });
}

export function createConversation(
  accessToken: string,
  payload: ConversationCreatePayload,
): Promise<ConversationSummary> {
  return apiPost<ConversationSummary, ConversationCreatePayload>("/conversations", payload, { accessToken });
}

export function getConversationDetail(
  accessToken: string,
  conversationId: string,
): Promise<ConversationDetail> {
  return apiGet<ConversationDetail>(`/conversations/${conversationId}`, { accessToken });
}

export function updateConversation(
  accessToken: string,
  conversationId: string,
  payload: ConversationUpdatePayload,
): Promise<ConversationSummary> {
  return apiPatch<ConversationSummary, ConversationUpdatePayload>(
    `/conversations/${conversationId}`, payload, { accessToken },
  );
}

export function deleteConversation(accessToken: string, conversationId: string): Promise<void> {
  return apiDelete(`/conversations/${conversationId}`, { accessToken });
}

export function addMessage(
  accessToken: string,
  conversationId: string,
  payload: MessageCreatePayload,
): Promise<MessageSummary> {
  return apiPost<MessageSummary, MessageCreatePayload>(
    `/conversations/${conversationId}/messages`, payload, { accessToken },
  );
}

export function addMessageCore(
  accessToken: string,
  conversationId: string,
  payload: MessageCreatePayload,
): Promise<AddMessageCoreResponse> {
  return apiPost<AddMessageCoreResponse, MessageCreatePayload>(
    `/conversations-core/${conversationId}/messages`, payload, { accessToken },
  );
}

export function generateAiReply(
  accessToken: string,
  conversationId: string,
): Promise<MessageSummary> {
  return apiPost<MessageSummary, Record<string, never>>(
    `/conversations/${conversationId}/ai-reply`, {}, { accessToken },
  );
}

export function processMessage(
  accessToken: string,
  conversationId: string,
  payload: ProcessMessagePayload,
): Promise<ProcessMessageResponse> {
  return apiPost<ProcessMessageResponse, ProcessMessagePayload>(
    `/conversations/${conversationId}/process-message`, payload, { accessToken },
  );
}

export function getTypingState(
  accessToken: string,
  conversationId: string,
): Promise<TypingState> {
  return apiGet<TypingState>(
    `/conversations/${conversationId}/typing`, { accessToken },
  );
}

export function regenerateAiReply(
  accessToken: string,
  conversationId: string,
): Promise<MessageSummary> {
  return apiPost<MessageSummary, Record<string, never>>(
    `/conversations/${conversationId}/regenerate-ai-reply`, {}, { accessToken },
  );
}
