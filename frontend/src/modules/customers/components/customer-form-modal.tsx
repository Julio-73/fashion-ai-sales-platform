"use client";

import { FormEvent, useEffect, useState } from "react";

import { t } from "@/lib/i18n";
import { Button } from "@/components/ui/button";
import { Modal } from "@/components/ui/modal";
import { statusLabel } from "@/modules/customers/components/customer-status-badge";
import type { CustomerCreatePayload, CustomerSummary, LeadStatus } from "@/types/customer";

type CustomerFormModalProps = {
  open: boolean;
  mode: "create" | "edit";
  customer: CustomerSummary | null;
  onOpenChange: (open: boolean) => void;
  onSubmit: (payload: CustomerCreatePayload) => Promise<void>;
};

const F = t.customers.form;
const statuses: LeadStatus[] = ["new", "interested", "negotiating", "won", "lost"];

const emptyForm: CustomerCreatePayload = {
  full_name: "",
  email: "",
  phone: "",
  whatsapp: "",
  instagram_username: "",
  tags: [],
  notes: "",
  lead_status: "new",
  source: "",
  assigned_to: null
};

export function CustomerFormModal({ open, mode, customer, onOpenChange, onSubmit }: CustomerFormModalProps) {
  const [form, setForm] = useState<CustomerCreatePayload>(emptyForm);
  const [tagInput, setTagInput] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  useEffect(() => {
    if (!open) return;
    setForm(
      customer
        ? {
            full_name: customer.full_name,
            email: customer.email ?? "",
            phone: customer.phone ?? "",
            whatsapp: customer.whatsapp ?? "",
            instagram_username: customer.instagram_username ?? "",
            tags: customer.tags,
            notes: customer.notes ?? "",
            lead_status: customer.lead_status,
            source: customer.source ?? "",
            assigned_to: customer.assigned_to ?? null
          }
        : emptyForm
    );
    setTagInput(customer?.tags.join(", ") ?? "");
    setSubmitError(null);
  }, [customer, open]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSubmitting(true);
    setSubmitError(null);
    try {
      await onSubmit({
        ...form,
        tags: tagInput
          .split(",")
          .map((tag) => tag.trim())
          .filter(Boolean),
        email: form.email || null,
        phone: form.phone || null,
        whatsapp: form.whatsapp || null,
        instagram_username: form.instagram_username || null,
        notes: form.notes || null,
        source: form.source || null
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
          <span className="text-sm font-medium">{F.fullName}</span>
          <input
            className="h-10 rounded-md border bg-background px-3 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
            value={form.full_name}
            onChange={(event) => setForm((current) => ({ ...current, full_name: event.target.value }))}
            required
          />
        </label>

        <div className="grid gap-4 sm:grid-cols-2">
          <label className="grid gap-1.5">
            <span className="text-sm font-medium">{F.email}</span>
            <input
              className="h-10 rounded-md border bg-background px-3 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
              type="email"
              value={form.email ?? ""}
              onChange={(event) => setForm((current) => ({ ...current, email: event.target.value }))}
            />
          </label>
          <label className="grid gap-1.5">
            <span className="text-sm font-medium">{F.leadStatus}</span>
            <select
              className="h-10 rounded-md border bg-background px-3 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
              value={form.lead_status}
              onChange={(event) =>
                setForm((current) => ({ ...current, lead_status: event.target.value as LeadStatus }))
              }
            >
              {statuses.map((status) => (
                <option key={status} value={status}>
                  {statusLabel[status]}
                </option>
              ))}
            </select>
          </label>
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <label className="grid gap-1.5">
            <span className="text-sm font-medium">{F.phone}</span>
            <input
              className="h-10 rounded-md border bg-background px-3 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
              value={form.phone ?? ""}
              onChange={(event) => setForm((current) => ({ ...current, phone: event.target.value }))}
            />
          </label>
          <label className="grid gap-1.5">
            <span className="text-sm font-medium">{F.whatsapp}</span>
            <input
              className="h-10 rounded-md border bg-background px-3 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
              value={form.whatsapp ?? ""}
              onChange={(event) => setForm((current) => ({ ...current, whatsapp: event.target.value }))}
            />
          </label>
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <label className="grid gap-1.5">
            <span className="text-sm font-medium">{F.instagram}</span>
            <input
              className="h-10 rounded-md border bg-background px-3 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
              value={form.instagram_username ?? ""}
              onChange={(event) => setForm((current) => ({ ...current, instagram_username: event.target.value }))}
            />
          </label>
          <label className="grid gap-1.5">
            <span className="text-sm font-medium">{F.source}</span>
            <input
              className="h-10 rounded-md border bg-background px-3 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
              value={form.source ?? ""}
              onChange={(event) => setForm((current) => ({ ...current, source: event.target.value }))}
            />
          </label>
        </div>

        <label className="grid gap-1.5">
          <span className="text-sm font-medium">{F.tags}</span>
          <input
            className="h-10 rounded-md border bg-background px-3 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
            value={tagInput}
            onChange={(event) => setTagInput(event.target.value)}
            placeholder={F.tagsPlaceholder}
          />
        </label>

        <label className="grid gap-1.5">
          <span className="text-sm font-medium">{F.notes}</span>
          <textarea
            className="min-h-24 rounded-md border bg-background px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
            value={form.notes ?? ""}
            onChange={(event) => setForm((current) => ({ ...current, notes: event.target.value }))}
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

