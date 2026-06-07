"use client";

import { ArrowDownRight, ArrowRight, ArrowUpRight, Minus } from "lucide-react";

import { cn } from "@/lib/utils";

type StatDeltaProps = {
  value: string;
  direction?: "up" | "down" | "flat";
  size?: "sm" | "md" | "lg";
  className?: string;
  showIcon?: boolean;
};

const sizeMap = {
  sm: "text-[10px] gap-0.5 px-1.5 py-0.5",
  md: "text-xs gap-1 px-2 py-0.5",
  lg: "text-sm gap-1 px-2.5 py-1"
};

const toneMap = {
  up: "bg-success-50 text-success ring-success-200 dark:bg-success-50/20 dark:text-success-200 dark:ring-success-200/30",
  down: "bg-destructive-50 text-destructive ring-destructive-100 dark:bg-destructive-50/20 dark:text-destructive-100 dark:ring-destructive-100/30",
  flat: "bg-secondary text-muted-foreground ring-border"
};

export function StatDelta({
  value,
  direction = "up",
  size = "md",
  className,
  showIcon = true
}: StatDeltaProps) {
  const Icon =
    direction === "up"
      ? ArrowUpRight
      : direction === "down"
        ? ArrowDownRight
        : Minus;
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-md font-medium ring-1 ring-inset",
        sizeMap[size],
        toneMap[direction],
        className
      )}
    >
      {showIcon ? (
        <Icon
          className={cn(
            size === "sm" ? "h-2.5 w-2.5" : "h-3 w-3"
          )}
          aria-hidden="true"
        />
      ) : null}
      {value}
    </span>
  );
}

export function StatNumber({
  value,
  label,
  hint,
  delta,
  className
}: {
  value: string | number;
  label?: string;
  hint?: string;
  delta?: { value: string; direction?: "up" | "down" | "flat" };
  className?: string;
}) {
  return (
    <div className={cn("space-y-1", className)}>
      {label ? <p className="eyebrow text-muted-foreground">{label}</p> : null}
      <p className="text-2xl font-semibold tracking-tight text-foreground">
        {value}
      </p>
      {(hint || delta) ? (
        <div className="flex items-center gap-2">
          {delta ? (
            <StatDelta
              value={delta.value}
              direction={delta.direction}
              size="sm"
            />
          ) : null}
          {hint ? (
            <span className="text-xs text-muted-foreground">{hint}</span>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}

export function InlineStat({
  label,
  value,
  trend,
  className
}: {
  label: string;
  value: string;
  trend?: { value: string; direction?: "up" | "down" | "flat" };
  className?: string;
}) {
  return (
    <div className={cn("flex items-baseline gap-2", className)}>
      <span className="text-xs text-muted-foreground">{label}</span>
      <span className="text-sm font-semibold tracking-tight">{value}</span>
      {trend ? (
        <StatDelta
          value={trend.value}
          direction={trend.direction}
          size="sm"
        />
      ) : null}
    </div>
  );
}

export function StatSeparator() {
  return <span aria-hidden="true" className="h-3 w-px bg-border" />;
}

export function ArrowRightIcon() {
  return <ArrowRight className="h-3 w-3" aria-hidden="true" />;
}
