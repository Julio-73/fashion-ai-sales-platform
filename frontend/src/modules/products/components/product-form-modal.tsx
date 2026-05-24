"use client";

import { FormEvent, useEffect, useState } from "react";

import { t } from "@/lib/i18n";
import { Button } from "@/components/ui/button";
import { Modal } from "@/components/ui/modal";
import { statusLabel } from "@/modules/products/components/product-status-badge";
import type { ProductCreatePayload, ProductStatus, ProductSummary } from "@/types/product";

type ProductFormModalProps = {
  open: boolean;
  mode: "create" | "edit";
  product: ProductSummary | null;
  onOpenChange: (open: boolean) => void;
  onSubmit: (payload: ProductCreatePayload) => Promise<void>;
};

const F = t.products.form;
const statuses: ProductStatus[] = ["active", "inactive", "draft"];

const emptyForm: ProductCreatePayload = {
  name: "",
  description: "",
  category: "",
  base_price: "",
  status: "draft"
};

export function ProductFormModal({ open, mode, product, onOpenChange, onSubmit }: ProductFormModalProps) {
  const [form, setForm] = useState<ProductCreatePayload>(emptyForm);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  useEffect(() => {
    if (!open) return;
    setForm(
      product
        ? {
            name: product.name,
            description: product.description ?? "",
            category: product.category ?? "",
            base_price: product.base_price ?? "",
            status: product.status
          }
        : emptyForm
    );
    setSubmitError(null);
  }, [product, open]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSubmitting(true);
    setSubmitError(null);
    try {
      await onSubmit({
        ...form,
        description: form.description || null,
        category: form.category || null,
        base_price: form.base_price || null
      });
      onOpenChange(false);
    } catch (err) {
      setSubmitError(err instanceof Error ? err.message : F.errorFallback);
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <Modal
      open={open}
      onOpenChange={onOpenChange}
      title={mode === "create" ? F.createTitle : F.editTitle}
      description={F.description}
    >
      <form className="grid gap-4" onSubmit={handleSubmit}>
        <label className="grid gap-1.5">
          <span className="text-sm font-medium">{F.productName}</span>
          <input
            className="h-10 rounded-md border bg-background px-3 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
            value={form.name}
            onChange={(event) => setForm((current) => ({ ...current, name: event.target.value }))}
            required
          />
        </label>

        <div className="grid gap-4 sm:grid-cols-2">
          <label className="grid gap-1.5">
            <span className="text-sm font-medium">{F.category}</span>
            <input
              className="h-10 rounded-md border bg-background px-3 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
              value={form.category ?? ""}
              onChange={(event) => setForm((current) => ({ ...current, category: event.target.value }))}
              placeholder={F.categoryPlaceholder}
            />
          </label>
          <label className="grid gap-1.5">
            <span className="text-sm font-medium">{F.status}</span>
            <select
              className="h-10 rounded-md border bg-background px-3 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
              value={form.status}
              onChange={(event) =>
                setForm((current) => ({ ...current, status: event.target.value as ProductStatus }))
              }
            >
              {statuses.map((s) => (
                <option key={s} value={s}>
                  {statusLabel[s]}
                </option>
              ))}
            </select>
          </label>
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <label className="grid gap-1.5">
            <span className="text-sm font-medium">{F.basePrice}</span>
            <input
              className="h-10 rounded-md border bg-background px-3 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
              type="number"
              step="0.01"
              min="0"
              value={form.base_price ?? ""}
              onChange={(event) => setForm((current) => ({ ...current, base_price: event.target.value }))}
              placeholder={F.pricePlaceholder}
            />
          </label>
        </div>

        <label className="grid gap-1.5">
          <span className="text-sm font-medium">{F.descriptionLabel}</span>
          <textarea
            className="min-h-24 rounded-md border bg-background px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
            value={form.description ?? ""}
            onChange={(event) => setForm((current) => ({ ...current, description: event.target.value }))}
            placeholder={F.descriptionPlaceholder}
          />
        </label>

        {submitError ? (
          <div className="rounded-lg border border-destructive/25 bg-destructive/10 px-4 py-3 text-sm text-destructive">
            {submitError}
          </div>
        ) : null}

        <div className="flex justify-end gap-2">
          <Button type="button" variant="ghost" onClick={() => onOpenChange(false)}>
            {F.cancel}
          </Button>
          <Button type="submit" disabled={isSubmitting}>
            {isSubmitting ? F.saving : F.save}
          </Button>
        </div>
      </form>
    </Modal>
  );
}
