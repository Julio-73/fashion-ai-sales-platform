import { t } from "@/lib/i18n";
import type { ProductStatus } from "@/types/product";

const statusLabel: Record<ProductStatus, string> = {
  active: t.products.status.active,
  inactive: t.products.status.inactive,
  draft: t.products.status.draft
};

const statusClass: Record<ProductStatus, string> = {
  active: "bg-emerald-50 text-emerald-700 ring-emerald-200",
  inactive: "bg-slate-100 text-slate-700 ring-slate-200",
  draft: "bg-amber-50 text-amber-700 ring-amber-200"
};

export function ProductStatusBadge({ status }: { status: ProductStatus }) {
  return (
    <span className={`inline-flex rounded-md px-2 py-1 text-xs font-medium ring-1 ${statusClass[status]}`}>
      {statusLabel[status]}
    </span>
  );
}

export { statusLabel };
