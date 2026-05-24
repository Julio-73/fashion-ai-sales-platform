export type ChatSummary = {
  id: string;
  empresa_id: string;
  cliente_id?: string | null;
  canal: "manual" | "whatsapp";
  estado: "open" | "pending" | "closed";
};

