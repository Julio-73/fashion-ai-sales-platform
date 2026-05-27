export type AILiveState = {
  ai_enabled: boolean;
  auto_reply_enabled: boolean;
  escalation_required: boolean;
  last_detected_intent: string | null;
  sentiment: string | null;
  urgency_score: number | null;
  lead_temperature: string | null;
  ai_last_response: string | null;
  ai_confidence: number | null;
};

export type AIStateResponse = {
  id: string;
  empresa_id: string;
  conversation_id: string;
  ai_enabled: boolean;
  auto_reply_enabled: boolean;
  escalation_required: boolean;
  last_detected_intent: string | null;
  sentiment: string | null;
  urgency_score: number | null;
  lead_temperature: string | null;
  ai_last_response: string | null;
  ai_confidence: number | null;
  created_at: string;
  updated_at: string;
};

export type SuggestedReply = {
  text: string;
  confidence: number;
  reasoning: string;
};

export type SuggestReplyResponse = {
  suggestions: SuggestedReply[];
};

export type ConversationInsightsResponse = {
  detected_intent: string;
  urgency: string;
  lead_score: number;
  probability_to_buy: number;
  recommended_action: string;
  escalation_recommended: boolean;
  customer_activity_level: string;
  last_interaction: string | null;
  suggested_next_step: string;
};

export type AIEventResponse = {
  id: string;
  empresa_id: string;
  conversation_id: string;
  event_type: string;
  payload: string | null;
  created_at: string;
};

export type AIEventListResponse = {
  events: AIEventResponse[];
  total: number;
};

export type HandoffResponse = {
  success: boolean;
  message: string;
};

export type IntentAnalysisResponse = {
  detected_intent: string;
  sentiment: string;
  urgency_score: number;
  lead_temperature: string;
  confidence: number;
};
