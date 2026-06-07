"use client";

import { motion } from "framer-motion";
import { type ReactNode, useState } from "react";

import { cn } from "@/lib/utils";

type TabItem = {
  value: string;
  label: string;
  icon?: ReactNode;
  badge?: ReactNode;
  count?: number;
};

type TabsProps = {
  items: TabItem[];
  value?: string;
  defaultValue?: string;
  onChange?: (value: string) => void;
  variant?: "underline" | "pills" | "segmented";
  className?: string;
  size?: "sm" | "md";
};

export function Tabs({
  items,
  value,
  defaultValue,
  onChange,
  variant = "underline",
  className,
  size = "md"
}: TabsProps) {
  const [internalValue, setInternalValue] = useState(
    defaultValue ?? items[0]?.value ?? ""
  );
  const current = value ?? internalValue;

  const handleSelect = (next: string) => {
    if (value === undefined) setInternalValue(next);
    onChange?.(next);
  };

  if (variant === "segmented") {
    return (
      <div
        role="tablist"
        className={cn(
          "inline-flex items-center gap-0.5 rounded-lg border bg-secondary/50 p-0.5",
          className
        )}
      >
        {items.map((item) => {
          const active = item.value === current;
          return (
            <button
              key={item.value}
              role="tab"
              type="button"
              aria-selected={active}
              onClick={() => handleSelect(item.value)}
              className={cn(
                "relative inline-flex items-center gap-2 rounded-md px-3 font-medium transition-colors",
                size === "sm" ? "h-7 text-xs" : "h-9 text-sm",
                active
                  ? "bg-card text-foreground shadow-sm"
                  : "text-muted-foreground hover:text-foreground"
              )}
            >
              {item.icon ? (
                <span aria-hidden="true">{item.icon}</span>
              ) : null}
              <span>{item.label}</span>
              {typeof item.count === "number" ? (
                <span
                  className={cn(
                    "rounded-full px-1.5 py-0.5 text-[10px] font-semibold",
                    active
                      ? "bg-primary-50 text-primary-700 dark:bg-primary-50/20 dark:text-primary-300"
                      : "bg-background text-muted-foreground"
                  )}
                >
                  {item.count}
                </span>
              ) : null}
              {item.badge ? (
                <span>{item.badge}</span>
              ) : null}
            </button>
          );
        })}
      </div>
    );
  }

  if (variant === "pills") {
    return (
      <div
        role="tablist"
        className={cn(
          "inline-flex flex-wrap items-center gap-1.5",
          className
        )}
      >
        {items.map((item) => {
          const active = item.value === current;
          return (
            <button
              key={item.value}
              role="tab"
              type="button"
              aria-selected={active}
              onClick={() => handleSelect(item.value)}
              className={cn(
                "inline-flex items-center gap-2 rounded-full border px-3.5 font-medium transition-all",
                size === "sm" ? "h-7 text-xs" : "h-9 text-sm",
                active
                  ? "border-primary-200 bg-primary-50 text-primary-700 shadow-sm dark:border-primary-300/30 dark:bg-primary-50/20 dark:text-primary-300"
                  : "border-border bg-card text-muted-foreground hover:border-primary-200 hover:text-foreground"
              )}
            >
              {item.icon ? (
                <span aria-hidden="true">{item.icon}</span>
              ) : null}
              <span>{item.label}</span>
              {typeof item.count === "number" ? (
                <span
                  className={cn(
                    "rounded-full px-1.5 py-0.5 text-[10px] font-semibold",
                    active
                      ? "bg-primary text-primary-foreground"
                      : "bg-secondary text-muted-foreground"
                  )}
                >
                  {item.count}
                </span>
              ) : null}
            </button>
          );
        })}
      </div>
    );
  }

  // underline (default)
  return (
    <div
      role="tablist"
      className={cn(
        "flex items-center gap-1 overflow-x-auto border-b scrollbar-hide",
        className
      )}
    >
      {items.map((item) => {
        const active = item.value === current;
        return (
          <button
            key={item.value}
            role="tab"
            type="button"
            aria-selected={active}
            onClick={() => handleSelect(item.value)}
            className={cn(
              "relative flex shrink-0 items-center gap-2 px-3 font-medium transition-colors",
              size === "sm" ? "h-9 text-xs" : "h-11 text-sm",
              active
                ? "text-foreground"
                : "text-muted-foreground hover:text-foreground"
            )}
          >
            {item.icon ? (
              <span aria-hidden="true">{item.icon}</span>
            ) : null}
            <span>{item.label}</span>
            {typeof item.count === "number" ? (
              <span
                className={cn(
                  "rounded-full px-1.5 py-0.5 text-[10px] font-semibold transition-colors",
                  active
                    ? "bg-primary-50 text-primary-700 dark:bg-primary-50/20 dark:text-primary-300"
                    : "bg-secondary text-muted-foreground"
                )}
              >
                {item.count}
              </span>
            ) : null}
            {active ? (
              <motion.span
                layoutId="tab-underline"
                className="absolute inset-x-0 -bottom-px h-0.5 rounded-t-full bg-primary"
                transition={{ type: "spring", stiffness: 380, damping: 30 }}
              />
            ) : null}
          </button>
        );
      })}
    </div>
  );
}
