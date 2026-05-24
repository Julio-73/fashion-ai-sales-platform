"use client";

import { motion } from "framer-motion";
import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";

type MetricCardProps = {
  title: string;
  value: string;
  icon: LucideIcon;
  footer?: ReactNode;
  trend?: string;
  delay?: number;
  className?: string;
};

export function MetricCard({ title, value, icon: Icon, footer, trend, delay = 0, className }: MetricCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.28, delay, ease: "easeOut" }}
      whileHover={{ y: -2 }}
      className={className}
    >
      <Card className="overflow-hidden transition-shadow hover:shadow-md">
        <CardHeader className="flex-row items-center justify-between space-y-0 pb-3">
          <CardTitle className="text-xs uppercase tracking-wide text-muted-foreground">{title}</CardTitle>
          <div className="flex h-9 w-9 items-center justify-center rounded-lg border bg-secondary text-primary">
            <Icon className="h-4 w-4" aria-hidden="true" />
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex items-end justify-between gap-3">
            <p className="text-2xl font-semibold tracking-normal">{value}</p>
            {trend ? (
              <span className={cn("rounded-md bg-emerald-50 px-2 py-1 text-xs font-medium text-emerald-700")}>
                {trend}
              </span>
            ) : null}
          </div>
          {footer ? <div className="mt-4">{footer}</div> : null}
        </CardContent>
      </Card>
    </motion.div>
  );
}

