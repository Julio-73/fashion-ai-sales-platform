import { t } from "@/lib/i18n";
import type { CustomerLifecycleStatus } from "@/types/crm";

const statusLabel: Record<CustomerLifecycleStatus, string> = {
  nuevo: t.crm.status.nuevo,
  activo: t.crm.status.activo,
  recurrente: t.crm.status.recurrente,
  vip: t.crm.status.vip,
  inactivo: t.crm.status.inactivo
};

const statusClass: Record<CustomerLifecycleStatus, string> = {
  nuevo: "bg-slate-100 text-slate-700 ring-slate-200",
  activo: "bg-emerald-50 text-emerald-700 ring-emerald-200",
  recurrente: "bg-blue-50 text-blue-700 ring-blue-200",
  vip: "bg-amber-50 text-amber-700 ring-amber-200",
  inactivo: "bg-rose-50 text-rose-700 ring-rose-200"
};

export function CustomerLifecycleBadge({
  status
}: {
  status: CustomerLifecycleStatus;
}) {
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs font-medium ring-1 ${statusClass[status]}`}
    >
      {status === "vip" ? <span aria-hidden="true">★</span> : null}
      {statusLabel[status]}
    </span>
  );
}

export { statusLabel as lifecycleStatusLabel };
