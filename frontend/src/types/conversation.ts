export type ConversationSummary = {
  id: string;
  empresa_id: string;
  cliente_id: string | null;
  asunto: string | null;
  canal: ConversationChannel;
  estado: ConversationStatus;
  deleted_at: string | null;
  created_at: string;
  updated_at: string;
};

export type ConversationChannel = "manual" | "whatsapp" | "instagram" | "facebook" | "web";

export type ConversationStatus = "open" | "pending" | "closed";

export type MessageSummary = {
  id: string;
  empresa_id: string;
  conversation_id: string;
  role: "agent" | "client" | "system";
  content: string;
  sender_name: string | null;
  extra_data: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
};

export type ConversationDetail = ConversationSummary & {
  messages: MessageSummary[];
};

export type ConversationListResponse = {
  items: ConversationSummary[];
  total: number;
  limit: number;
  offset: number;
};

export type ConversationCreatePayload = {
  cliente_id?: string | null;
  asunto?: string | null;
  canal: ConversationChannel;
};

export type ConversationUpdatePayload = {
  asunto?: string | null;
  canal?: ConversationChannel;
  estado?: ConversationStatus;
};

export type MessageCreatePayload = {
  role: "agent" | "client" | "system";
  content: string;
  sender_name?: string | null;
  extra_data?: Record<string, unknown> | null;
};

export type AddMessageCoreResponse = {
  message: MessageSummary;
  ai_reply: MessageSummary | null;
};

export type TypingState = {
  is_typing: boolean;
};

export type ProcessMessageResponse = {
  message: MessageSummary;
  ai_reply: MessageSummary | null;
  typing: TypingState;
};

export type ProcessMessagePayload = {
  content: string;
  role: "agent" | "client" | "system";
  sender_name?: string | null;
};
