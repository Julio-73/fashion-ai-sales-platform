"use client";

import { motion } from "framer-motion";
import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

type EmptyStateAction =
  | ReactNode
  | { label: string; onClick?: () => void };

type EmptyStateProps = {
  title: string;
  description?: string;
  icon?: LucideIcon;
  action?: EmptyStateAction;
  className?: string;
  variant?: "default" | "minimal" | "centered";
};

export function EmptyState({
  title,
  description,
  icon: Icon,
  action,
  className,
  variant = "default"
}: EmptyStateProps) {
  const renderedAction =
    action && typeof action === "object" && "label" in action ? (
      <Button type="button" onClick={action.onClick}>
        {action.label}
      </Button>
    ) : (
      action
    );

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
      className={cn(
        "card-surface flex flex-col items-center text-center",
        variant === "default" && "px-6 py-12",
        variant === "centered" && "min-h-[320px] justify-center px-6 py-16",
        variant === "minimal" && "px-4 py-8",
        className
      )}
    >
      {Icon ? (
        <div
          className={cn(
            "mb-5 flex items-center justify-center rounded-2xl",
            "bg-gradient-to-br from-primary-50 to-primary-100",
            "ring-1 ring-primary-200/50",
            "shadow-inner",
            variant === "minimal" ? "h-10 w-10" : "h-14 w-14"
          )}
          aria-hidden="true"
        >
          <Icon
            className={cn(
              "text-primary",
              variant === "minimal" ? "h-5 w-5" : "h-6 w-6"
            )}
          />
        </div>
      ) : null}
      <h3
        className={cn(
          "font-semibold text-foreground",
          variant === "minimal" ? "text-sm" : "text-base"
        )}
      >
        {title}
      </h3>
      {description ? (
        <p
          className={cn(
            "mt-1.5 max-w-md text-sm leading-6 text-muted-foreground",
            variant === "minimal" && "text-xs"
          )}
        >
          {description}
        </p>
      ) : null}
      {renderedAction ? <div className="mt-5">{renderedAction}</div> : null}
    </motion.div>
  );
}
