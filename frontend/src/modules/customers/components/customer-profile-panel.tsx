import { useState } from "react";
import { Instagram, Mail, MessageCircle, Phone, UserRound } from "lucide-react";

import { t } from "@/lib/i18n";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { CustomerStatusBadge } from "@/modules/customers/components/customer-status-badge";
import type { CustomerSummary } from "@/types/customer";

const P = t.customers.profile;

type CustomerProfilePanelProps = {
  customer: CustomerSummary | null;
  onEdit: (customer: CustomerSummary) => void;
  onDelete: (customer: CustomerSummary) => Promise<void>;
};

export function CustomerProfilePanel({ customer, onEdit, onDelete }: CustomerProfilePanelProps) {
  const [isDeleting, setIsDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);
  if (!customer) {
    return (
      <Card className="h-full">
        <CardHeader>
          <CardTitle>{P.emptyTitle}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="rounded-lg border border-dashed p-6 text-sm leading-6 text-muted-foreground">
            {P.emptyDesc}
          </div>
        </CardContent>
      </Card>
    );
  }

  const contactItems = [
    { label: P.email, value: customer.email, icon: Mail },
    { label: P.phone, value: customer.phone, icon: Phone },
    { label: P.whatsapp, value: customer.whatsapp, icon: MessageCircle },
    { label: P.instagram, value: customer.instagram_username, icon: Instagram }
  ];

  return (
    <Card className="h-full">
      <CardHeader className="border-b">
        <div className="flex items-start justify-between gap-4">
          <div>
            <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-lg bg-secondary text-primary">
              <UserRound className="h-5 w-5" aria-hidden="true" />
            </div>
            <CardTitle>{customer.full_name}</CardTitle>
            <p className="mt-1 text-sm text-muted-foreground">{customer.source ?? P.noSource}</p>
          </div>
          <CustomerStatusBadge status={customer.lead_status} />
        </div>
      </CardHeader>
      <CardContent className="grid gap-5 pt-5">
        <div className="grid gap-3">
          {contactItems.map((item) => (
            <div key={item.label} className="flex items-center gap-3 rounded-lg border bg-background px-3 py-2">
              <item.icon className="h-4 w-4 text-muted-foreground" aria-hidden="true" />
              <div className="min-w-0">
                <p className="text-xs text-muted-foreground">{item.label}</p>
                <p className="truncate text-sm font-medium">{item.value || P.notProvided}</p>
              </div>
            </div>
          ))}
        </div>

        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">{P.tags}</p>
          <div className="mt-2 flex flex-wrap gap-2">
            {customer.tags.length ? (
              customer.tags.map((tag) => (
                <span key={tag} className="rounded-md bg-secondary px-2 py-1 text-xs font-medium">
                  {tag}
                </span>
              ))
            ) : (
              <span className="text-sm text-muted-foreground">{P.noTags}</span>
            )}
          </div>
        </div>

        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">{P.notes}</p>
          <p className="mt-2 rounded-lg border bg-background p-3 text-sm leading-6 text-muted-foreground">
            {customer.notes || P.noNotes}
          </p>
        </div>

        {deleteError ? (
          <div className="rounded-lg border border-destructive/25 bg-destructive/10 px-4 py-3 text-sm text-destructive">
            {deleteError}
          </div>
        ) : null}

        <div className="grid gap-2 sm:grid-cols-2">
          <Button type="button" variant="secondary" onClick={() => onEdit(customer)}>
            {P.edit}
          </Button>
          <Button
            type="button"
            variant="outline"
            disabled={isDeleting}
            onClick={async () => {
              setIsDeleting(true);
              setDeleteError(null);
              try {
                await onDelete(customer);
              } catch (err) {
                setDeleteError(err instanceof Error ? err.message : P.errorDelete);
              } finally {
                setIsDeleting(false);
              }
            }}
          >
            {isDeleting ? P.deleting : P.delete}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

