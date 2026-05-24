import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

import { Button } from "@/components/ui/button";

type EmptyStateProps = {
  title: string;
  description: string;
  icon?: LucideIcon;
  action?: {
    label: string;
    onClick?: () => void;
  };
  children?: ReactNode;
};

export function EmptyState({ title, description, icon: Icon, action, children }: EmptyStateProps) {
  return (
    <div className="rounded-lg border bg-card p-8 text-center shadow-sm">
      {Icon ? (
        <div className="mx-auto mb-4 flex h-11 w-11 items-center justify-center rounded-lg bg-secondary text-primary">
          <Icon className="h-5 w-5" aria-hidden="true" />
        </div>
      ) : null}
      <h2 className="text-base font-semibold text-card-foreground">{title}</h2>
      <p className="mx-auto mt-2 max-w-xl text-sm leading-6 text-muted-foreground">{description}</p>
      {children ? <div className="mt-5">{children}</div> : null}
      {action ? (
        <div className="mt-5">
          <Button type="button" variant="secondary" onClick={action.onClick}>
            {action.label}
          </Button>
        </div>
      ) : null}
    </div>
  );
}

