import { cva, type VariantProps } from "class-variance-authority";
import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

const statusPillVariants = cva(
  "inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset transition-colors",
  {
    variants: {
      tone: {
        neutral:
          "bg-secondary text-secondary-foreground ring-border",
        primary:
          "bg-primary-50 text-primary-700 ring-primary-200 dark:bg-primary-50/20 dark:text-primary-300 dark:ring-primary-300/30",
        success:
          "bg-success-50 text-success ring-success-200 dark:bg-success-50/20 dark:text-success-200 dark:ring-success-200/30",
        warning:
          "bg-warning-50 text-warning ring-warning-200 dark:bg-warning-50/20 dark:text-warning-200 dark:ring-warning-200/30",
        info: "bg-info-50 text-info ring-info-100 dark:bg-info-50/20 dark:text-info-200 dark:ring-info-100/30",
        destructive:
          "bg-destructive-50 text-destructive ring-destructive-100 dark:bg-destructive-50/20 dark:text-destructive-100 dark:ring-destructive-100/30",
        purple:
          "bg-purple/10 text-purple ring-purple/20 dark:text-purple dark:ring-purple/30",
        vip:
          "bg-gradient-to-r from-amber-100 to-rose-100 text-amber-800 ring-amber-200 dark:from-amber-950/50 dark:to-rose-950/50 dark:text-amber-200 dark:ring-amber-800/30"
      },
      size: {
        sm: "text-[10px] px-2 py-0.5",
        md: "text-xs px-2.5 py-0.5",
        lg: "text-sm px-3 py-1"
      }
    },
    defaultVariants: {
      tone: "neutral",
      size: "md"
    }
  }
);

type StatusPillProps = {
  children: ReactNode;
  dot?: boolean;
  icon?: ReactNode;
  className?: string;
} & VariantProps<typeof statusPillVariants>;

export function StatusPill({
  children,
  tone,
  size,
  dot,
  icon,
  className
}: StatusPillProps) {
  const dotColor = {
    neutral: "bg-muted-foreground",
    primary: "bg-primary",
    success: "bg-success",
    warning: "bg-warning",
    info: "bg-info",
    destructive: "bg-destructive",
    purple: "bg-purple",
    vip: "bg-amber-500"
  }[tone || "neutral"];

  return (
    <span
      className={cn(statusPillVariants({ tone, size }), className)}
    >
      {dot ? (
        <span
          aria-hidden="true"
          className={cn("h-1.5 w-1.5 rounded-full", dotColor)}
        />
      ) : null}
      {icon ? <span aria-hidden="true">{icon}</span> : null}
      {children}
    </span>
  );
}
