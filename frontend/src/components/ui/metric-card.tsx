"use client";

import { motion } from "framer-motion";
import { ArrowDownRight, ArrowUpRight } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

type MetricCardProps = {
  title: string;
  value: string;
  icon: LucideIcon;
  footer?: ReactNode;
  trend?: string;
  trendDirection?: "up" | "down" | "flat";
  delay?: number;
  className?: string;
  iconTone?: "primary" | "success" | "warning" | "info" | "purple" | "pink" | "cyan" | "destructive";
  variant?: "default" | "elevated" | "glow";
  description?: ReactNode;
  sparkline?: number[];
};

const iconToneMap = {
  primary: {
    bg: "bg-primary-50 text-primary dark:bg-primary-50/20 dark:text-primary-300",
    ring: "ring-primary-200/60 dark:ring-primary-300/20"
  },
  success: {
    bg: "bg-success-50 text-success dark:bg-success-50/20 dark:text-success-200",
    ring: "ring-success-200/60 dark:ring-success-200/20"
  },
  warning: {
    bg: "bg-warning-50 text-warning dark:bg-warning-50/20 dark:text-warning-200",
    ring: "ring-warning-200/60 dark:ring-warning-200/20"
  },
  info: {
    bg: "bg-info-50 text-info dark:bg-info-50/20 dark:text-info-200",
    ring: "ring-info-100/60 dark:ring-info-100/20"
  },
  purple: {
    bg: "bg-purple/10 text-purple dark:bg-purple/20 dark:text-purple",
    ring: "ring-purple/20"
  },
  pink: {
    bg: "bg-pink/10 text-pink dark:bg-pink/20 dark:text-pink",
    ring: "ring-pink/20"
  },
  cyan: {
    bg: "bg-cyan/10 text-cyan dark:bg-cyan/20 dark:text-cyan",
    ring: "ring-cyan/20"
  },
  destructive: {
    bg: "bg-destructive-50 text-destructive dark:bg-destructive-50/20 dark:text-destructive-100",
    ring: "ring-destructive-100/60 dark:ring-destructive-100/20"
  }
};

export function MetricCard({
  title,
  value,
  icon: Icon,
  footer,
  trend,
  trendDirection = "up",
  delay = 0,
  className,
  iconTone = "primary",
  variant = "default",
  description,
  sparkline
}: MetricCardProps) {
  const TrendIcon =
    trendDirection === "down" ? ArrowDownRight : ArrowUpRight;
  const trendTone =
    trendDirection === "down"
      ? "bg-destructive-50 text-destructive ring-destructive-100"
      : trendDirection === "up"
        ? "bg-success-50 text-success ring-success-200"
        : "bg-secondary text-muted-foreground ring-border";

  const variantMap = {
    default: "card-surface",
    elevated: "card-elevated",
    glow: "card-glow"
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay, ease: [0.16, 1, 0.3, 1] }}
      whileHover={{ y: -2 }}
      className={cn("group", className)}
    >
      <div
        className={cn(
          variantMap[variant],
          "p-5 transition-shadow hover:shadow-md"
        )}
      >
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0 flex-1">
            <p className="eyebrow text-muted-foreground">{title}</p>
            <p className="mt-2 text-2xl font-semibold tracking-tight text-foreground">
              {value}
            </p>
            {description ? (
              <p className="mt-1 text-xs text-muted-foreground">
                {description}
              </p>
            ) : null}
          </div>
          <div
            className={cn(
              "flex h-10 w-10 shrink-0 items-center justify-center rounded-xl ring-1 transition-transform group-hover:scale-105",
              iconToneMap[iconTone].bg,
              iconToneMap[iconTone].ring
            )}
          >
            <Icon className="h-4 w-4" aria-hidden="true" />
          </div>
        </div>

        {(trend || sparkline) && (
          <div className="mt-4 flex items-end justify-between gap-3">
            {trend ? (
              <span
                className={cn(
                  "inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-xs font-medium ring-1",
                  trendTone
                )}
              >
                <TrendIcon
                  className={cn(
                    "h-3 w-3",
                    trendDirection === "flat" && "hidden"
                  )}
                  aria-hidden="true"
                />
                {trend}
              </span>
            ) : (
              <span />
            )}
            {sparkline ? <Sparkline values={sparkline} /> : null}
          </div>
        )}

        {footer ? <div className="mt-4">{footer}</div> : null}
      </div>
    </motion.div>
  );
}

function Sparkline({ values }: { values: number[] }) {
  if (values.length === 0) return null;
  const max = Math.max(...values, 1);
  const min = Math.min(...values, 0);
  const range = max - min || 1;
  const width = 80;
  const height = 28;
  const step = width / (values.length - 1 || 1);
  const points = values
    .map((v, i) => {
      const x = i * step;
      const y = height - ((v - min) / range) * height;
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");

  return (
    <svg
      width={width}
      height={height}
      viewBox={`0 0 ${width} ${height}`}
      fill="none"
      className="overflow-visible"
      aria-hidden="true"
    >
      <defs>
        <linearGradient id="sparkline-gradient" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="hsl(var(--primary))" stopOpacity="0.25" />
          <stop offset="100%" stopColor="hsl(var(--primary))" stopOpacity="0" />
        </linearGradient>
      </defs>
      <polyline
        points={`0,${height} ${points} ${width},${height}`}
        fill="url(#sparkline-gradient)"
        stroke="none"
      />
      <polyline
        points={points}
        fill="none"
        stroke="hsl(var(--primary))"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
