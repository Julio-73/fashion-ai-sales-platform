export type CustomerSummary = {
  id: string;
  empresa_id: string;
  full_name: string;
  email?: string | null;
  phone?: string | null;
  whatsapp?: string | null;
  instagram_username?: string | null;
  tags: string[];
  notes?: string | null;
  lead_status: LeadStatus;
  source?: string | null;
  assigned_to?: string | null;
  created_at: string;
  updated_at: string;
};

export type LeadStatus = "new" | "interested" | "negotiating" | "won" | "lost";

export type CustomerListResponse = {
  items: CustomerSummary[];
  total: number;
  limit: number;
  offset: number;
};

export type CustomerCreatePayload = {
  full_name: string;
  email?: string | null;
  phone?: string | null;
  whatsapp?: string | null;
  instagram_username?: string | null;
  tags: string[];
  notes?: string | null;
  lead_status: LeadStatus;
  source?: string | null;
  assigned_to?: string | null;
};

export type CustomerUpdatePayload = Partial<CustomerCreatePayload>;
