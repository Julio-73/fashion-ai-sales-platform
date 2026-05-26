export type LeadStatus = "new" | "interested" | "negotiating" | "won" | "lost";
export type CustomerPriority = "hot" | "warm" | "cool" | "cold";
export type ActivityLevel = "very_active" | "active" | "moderate" | "low" | "inactive";
export type ConversionProbability = "high" | "medium" | "low";
export type IntentType = "purchase_intent" | "pricing_intent" | "negotiation_intent" | "shipping_intent" | "greeting" | "complaint" | "goodbye" | "unknown";

export type TopCustomer = {
  customer_id: string;
  full_name: string;
  lead_score: number;
  priority: CustomerPriority;
  lead_status: LeadStatus;
  last_interaction_at: string | null;
};

export type IntentCount = {
  intent: string;
  count: number;
};

export type SalesInsightsResponse = {
  total_hot_leads: number;
  total_interested: number;
  total_negotiation: number;
  total_converted: number;
  top_customers: TopCustomer[];
  high_priority_customers: TopCustomer[];
  most_detected_intents: IntentCount[];
  recent_sales_activity: number;
};

export type TopLead = {
  customer_id: string;
  full_name: string;
  lead_score: number;
  priority: CustomerPriority;
  lead_status: LeadStatus;
  conversation_count: number;
  last_interaction_at: string | null;
  conversion_probability: ConversionProbability;
};

export type TopLeadsResponse = {
  leads: TopLead[];
  total: number;
};

export type CustomerRecommendation = {
  customer_id: string;
  full_name: string;
  lead_score: number;
  priority: CustomerPriority;
  lead_status: LeadStatus;
  reason: string;
  days_since_last_interaction: number | null;
};

export type SalesRecommendationsResponse = {
  customers_to_follow_up: CustomerRecommendation[];
  hot_leads: CustomerRecommendation[];
  negotiation_leads: CustomerRecommendation[];
  inactive_customers: CustomerRecommendation[];
  upsell_opportunities: CustomerRecommendation[];
};

export type ConversationMetrics = {
  total_conversations: number;
  total_messages: number;
  last_message_at: string | null;
  last_message_content: string | null;
};

export type CustomerSalesProfileResponse = {
  customer_id: string;
  full_name: string;
  email: string;
  phone: string;
  lead_score: number;
  lead_status: LeadStatus;
  priority: CustomerPriority;
  tags: string[];
  detected_intents: string[];
  activity_level: ActivityLevel;
  last_interaction_at: string | null;
  conversation_metrics: ConversationMetrics;
  sales_summary: string;
};

export type ActivityEvent = {
  event_type: string;
  description: string;
  timestamp: string;
  customer_id: string;
  customer_name: string | null;
};

export type SalesActivityResponse = {
  events: ActivityEvent[];
  total: number;
};

export type AnalyzeMessageResponse = {
  detected_intent: string;
  score_impact: number;
  recommended_action: string;
  lead_status_prediction: string;
};
