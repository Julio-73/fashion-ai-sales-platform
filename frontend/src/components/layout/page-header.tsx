"use client";

import type { ReactNode } from "react";

import { Breadcrumbs, type BreadcrumbItem } from "@/components/ui/breadcrumbs";
import { StatusPill } from "@/components/ui/status-pill";
import { cn } from "@/lib/utils";

type PageHeaderProps = {
  eyebrow?: string;
  title: string;
  description?: string;
  breadcrumbs?: BreadcrumbItem[];
  status?: {
    label: string;
    tone?: "success" | "warning" | "info" | "neutral";
  };
  actions?: ReactNode;
  meta?: ReactNode;
  className?: string;
};

export function PageHeader({
  eyebrow,
  title,
  description,
  breadcrumbs,
  status,
  actions,
  meta,
  className
}: PageHeaderProps) {
  return (
    <header
      className={cn(
        "relative overflow-hidden rounded-2xl border bg-gradient-to-br from-card via-card to-secondary/40 px-6 py-5 shadow-sm",
        className
      )}
    >
      <div
        aria-hidden="true"
        className="pointer-events-none absolute -right-12 -top-16 h-44 w-44 rounded-full bg-primary-100/40 blur-3xl dark:bg-primary-300/10"
      />
      <div
        aria-hidden="true"
        className="pointer-events-none absolute -bottom-20 right-1/3 h-40 w-40 rounded-full bg-purple/10 blur-3xl dark:bg-purple/5"
      />

      <div className="relative">
        {breadcrumbs && breadcrumbs.length > 0 ? (
          <Breadcrumbs items={breadcrumbs} className="mb-3" />
        ) : null}

        <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-2">
              {eyebrow ? (
                <span className="eyebrow text-primary">{eyebrow}</span>
              ) : null}
              {status ? (
                <StatusPill tone={status.tone} dot>
                  {status.label}
                </StatusPill>
              ) : null}
            </div>
            <h1 className="mt-1.5 text-2xl font-semibold tracking-tight text-foreground md:text-[28px]">
              {title}
            </h1>
            {description ? (
              <p className="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">
                {description}
              </p>
            ) : null}
            {meta ? <div className="mt-3 flex flex-wrap items-center gap-3">{meta}</div> : null}
          </div>
          {actions ? (
            <div className="flex shrink-0 flex-wrap items-center gap-2">
              {actions}
            </div>
          ) : null}
        </div>
      </div>
    </header>
  );
}
