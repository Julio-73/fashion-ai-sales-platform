import { ChevronRight, Home } from "lucide-react";
import Link from "next/link";
import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

export type BreadcrumbItem = {
  label: string;
  href?: string;
  icon?: ReactNode;
};

type BreadcrumbsProps = {
  items: BreadcrumbItem[];
  className?: string;
};

export function Breadcrumbs({ items, className }: BreadcrumbsProps) {
  return (
    <nav
      aria-label="Breadcrumb"
      className={cn(
        "flex items-center gap-1 text-xs text-muted-foreground",
        className
      )}
    >
      <ol className="flex flex-wrap items-center gap-1">
        {items.map((item, index) => {
          const isLast = index === items.length - 1;
          const isFirst = index === 0;
          return (
            <li
              key={`${item.label}-${index}`}
              className="flex items-center gap-1"
            >
              {item.href && !isLast ? (
                <Link
                  href={item.href}
                  className={cn(
                    "inline-flex items-center gap-1 rounded-md px-1.5 py-0.5 transition-colors hover:bg-secondary hover:text-foreground",
                    isFirst && "text-foreground/70"
                  )}
                >
                  {isFirst && !item.icon ? (
                    <Home className="h-3 w-3" aria-hidden="true" />
                  ) : item.icon ? (
                    <span aria-hidden="true">{item.icon}</span>
                  ) : null}
                  <span>{item.label}</span>
                </Link>
              ) : (
                <span
                  className={cn(
                    "inline-flex items-center gap-1 px-1.5 py-0.5",
                    isLast && "font-medium text-foreground"
                  )}
                  aria-current={isLast ? "page" : undefined}
                >
                  {isFirst && !item.icon ? (
                    <Home className="h-3 w-3" aria-hidden="true" />
                  ) : item.icon ? (
                    <span aria-hidden="true">{item.icon}</span>
                  ) : null}
                  <span className="truncate max-w-[180px]">{item.label}</span>
                </span>
              )}
              {!isLast ? (
                <ChevronRight
                  className="h-3 w-3 shrink-0 text-muted-foreground/60"
                  aria-hidden="true"
                />
              ) : null}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
