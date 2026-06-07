import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

type SectionHeaderProps = {
  title: string;
  description?: string;
  action?: ReactNode;
  eyebrow?: string;
  className?: string;
  children?: ReactNode;
};

export function SectionHeader({
  title,
  description,
  action,
  eyebrow,
  className,
  children
}: SectionHeaderProps) {
  return (
    <div className={cn("flex flex-col gap-3", className)}>
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          {eyebrow ? (
            <p className="eyebrow mb-1 text-muted-foreground">{eyebrow}</p>
          ) : null}
          <h2 className="text-base font-semibold tracking-tight text-foreground md:text-lg">
            {title}
          </h2>
          {description ? (
            <p className="mt-1 text-sm leading-6 text-muted-foreground">
              {description}
            </p>
          ) : null}
        </div>
        {action ? <div className="shrink-0">{action}</div> : null}
      </div>
      {children}
    </div>
  );
}
