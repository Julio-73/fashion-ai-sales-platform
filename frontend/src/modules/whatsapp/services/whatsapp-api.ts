import { apiGet, apiPost } from "@/services/api-client";
import type {
  WhatsappAccount,
  WhatsappAccountCreatePayload,
  WhatsappMessage,
  WhatsappMessageListResponse,
  WhatsappMetrics,
  WhatsappSendPayload,
  WhatsappWebhookListResponse,
} from "@/types/whatsapp";

export type WhatsappSendResponse = {
  message: WhatsappMessage;
  accepted: boolean;
  provider_response: Record<string, unknown> | null;
};

export function getWhatsappMetrics(accessToken: string): Promise<WhatsappMetrics> {
  return apiGet<WhatsappMetrics>("/whatsapp/metrics", { accessToken });
}

export function listWhatsappAccounts(accessToken: string): Promise<WhatsappAccount[]> {
  return apiGet<WhatsappAccount[]>("/whatsapp/accounts", { accessToken });
}

export function createWhatsappAccount(
  accessToken: string,
  payload: WhatsappAccountCreatePayload,
): Promise<WhatsappAccount> {
  return apiPost<WhatsappAccount, WhatsappAccountCreatePayload>(
    "/whatsapp/accounts",
    payload,
    { accessToken },
  );
}

export function listWhatsappMessages(
  accessToken: string,
  params: { limit?: number; offset?: number; direction?: "inbound" | "outbound" } = {},
): Promise<WhatsappMessageListResponse> {
  const query = new URLSearchParams();
  query.set("limit", String(params.limit ?? 25));
  query.set("offset", String(params.offset ?? 0));
  if (params.direction) query.set("direction", params.direction);
  return apiGet<WhatsappMessageListResponse>(
    `/whatsapp/messages?${query.toString()}`,
    { accessToken },
  );
}

export function listWhatsappWebhooks(
  accessToken: string,
  params: { limit?: number; offset?: number } = {},
): Promise<WhatsappWebhookListResponse> {
  const query = new URLSearchParams();
  query.set("limit", String(params.limit ?? 25));
  query.set("offset", String(params.offset ?? 0));
  return apiGet<WhatsappWebhookListResponse>(
    `/whatsapp/webhooks?${query.toString()}`,
    { accessToken },
  );
}

export function sendWhatsappMessage(
  accessToken: string,
  payload: WhatsappSendPayload,
): Promise<WhatsappSendResponse> {
  return apiPost<WhatsappSendResponse, WhatsappSendPayload>(
    "/whatsapp/send",
    payload,
    { accessToken },
  );
}
