export type WhatsappDirection = "inbound" | "outbound";
export type WhatsappMessageStatus = "pending" | "sent" | "delivered" | "read" | "failed";
export type WhatsappWebhookEvent = "verification" | "message" | "status" | "unknown";

export type WhatsappAccount = {
  id: string;
  empresa_id: string;
  phone_number_id: string;
  business_account_id: string | null;
  display_phone_number: string | null;
  verified_name: string | null;
  api_version: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type WhatsappWebhook = {
  id: string;
  empresa_id: string | null;
  phone_number_id: string | null;
  event_type: WhatsappWebhookEvent;
  processed: boolean;
  error: string | null;
  received_at: string;
  created_at: string;
};

export type WhatsappMessage = {
  id: string;
  empresa_id: string;
  account_id: string;
  conversation_id: string | null;
  direction: WhatsappDirection;
  wa_message_id: string | null;
  from_phone: string;
  to_phone: string;
  body: string | null;
  message_type: string;
  status: WhatsappMessageStatus;
  error: string | null;
  created_at: string;
  updated_at: string;
};

export type WhatsappMetrics = {
  is_configured: boolean;
  active_accounts: number;
  inbound_total: number;
  outbound_total: number;
  delivered_total: number;
  failed_total: number;
  pending_total: number;
  inbound_last_24h: number;
  outbound_last_24h: number;
  webhooks_last_24h: number;
  webhooks_failed_last_24h: number;
  recent_webhooks: WhatsappWebhook[];
};

export type WhatsappMessageListResponse = {
  items: WhatsappMessage[];
  total: number;
  limit: number;
  offset: number;
};

export type WhatsappWebhookListResponse = {
  items: WhatsappWebhook[];
  total: number;
  limit: number;
  offset: number;
};

export type WhatsappSendPayload = {
  to_phone: string;
  body: string;
  account_id?: string;
  conversation_id?: string;
};

export type WhatsappAccountCreatePayload = {
  phone_number_id: string;
  business_account_id?: string;
  display_phone_number?: string;
  verified_name?: string;
  access_token?: string;
  webhook_verify_token: string;
  api_version?: string;
  is_active?: boolean;
};
