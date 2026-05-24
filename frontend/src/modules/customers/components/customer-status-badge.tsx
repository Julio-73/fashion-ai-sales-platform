import { t } from "@/lib/i18n";
import type { LeadStatus } from "@/types/customer";

const statusLabel: Record<LeadStatus, string> = {
  new: t.customers.status.new,
  interested: t.customers.status.interested,
  negotiating: t.customers.status.negotiating,
  won: t.customers.status.won,
  lost: t.customers.status.lost
};

const statusClass: Record<LeadStatus, string> = {
  new: "bg-slate-100 text-slate-700 ring-slate-200",
  interested: "bg-blue-50 text-blue-700 ring-blue-200",
  negotiating: "bg-amber-50 text-amber-700 ring-amber-200",
  won: "bg-emerald-50 text-emerald-700 ring-emerald-200",
  lost: "bg-rose-50 text-rose-700 ring-rose-200"
};

export function CustomerStatusBadge({ status }: { status: LeadStatus }) {
  return (
    <span className={`inline-flex rounded-md px-2 py-1 text-xs font-medium ring-1 ${statusClass[status]}`}>
      {statusLabel[status]}
    </span>
  );
}

export { statusLabel };

