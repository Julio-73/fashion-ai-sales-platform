"use client";

import { useEffect, useState } from "react";
import {
  AlertTriangle,
  CheckCircle2,
  Info,
  type LucideIcon
} from "lucide-react";

type ToastProps = {
  id: string;
  title: string;
  description?: string;
  tone?: "success" | "error" | "info" | "warning";
  duration?: number;
  onDismiss: (id: string) => void;
};

const toneMap = {
  success: {
    icon: CheckCircle2,
    ring: "ring-success-200",
    bg: "bg-success-50/80 dark:bg-success-50/10",
    iconColor: "text-success"
  },
  error: {
    icon: AlertTriangle,
    ring: "ring-destructive-100",
    bg: "bg-destructive-50/80 dark:bg-destructive-50/10",
    iconColor: "text-destructive"
  },
  info: {
    icon: Info,
    ring: "ring-info-100",
    bg: "bg-info-50/80 dark:bg-info-50/10",
    iconColor: "text-info"
  },
  warning: {
    icon: AlertTriangle,
    ring: "ring-warning-200",
    bg: "bg-warning-50/80 dark:bg-warning-50/10",
    iconColor: "text-warning"
  }
};

export function Toast({
  id,
  title,
  description,
  tone = "info",
  duration = 4000,
  onDismiss
}: ToastProps) {
  const t = toneMap[tone];
  const Icon: LucideIcon = t.icon;
  useEffect(() => {
    const t = setTimeout(() => onDismiss(id), duration);
    return () => clearTimeout(t);
  }, [id, duration, onDismiss]);

  return (
    <div
      role="status"
      className={`flex items-start gap-3 rounded-xl border ${t.bg} ${t.ring} p-3.5 shadow-lg backdrop-blur anim-slide-in-right`}
    >
      <Icon className={`h-4 w-4 shrink-0 ${t.iconColor}`} aria-hidden="true" />
      <div className="min-w-0 flex-1">
        <p className="text-sm font-medium">{title}</p>
        {description ? (
          <p className="mt-0.5 text-xs text-muted-foreground">{description}</p>
        ) : null}
      </div>
    </div>
  );
}

type ToastData = {
  id: string;
  title: string;
  description?: string;
  tone?: "success" | "error" | "info" | "warning";
};

export function useToasts() {
  const [toasts, setToasts] = useState<ToastData[]>([]);

  const push = (toast: Omit<ToastData, "id">) => {
    setToasts((prev) => [...prev, { ...toast, id: String(Date.now()) }]);
  };

  const dismiss = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  return { toasts, push, dismiss };
}

export function Toaster({ toasts, onDismiss }: { toasts: ToastData[]; onDismiss: (id: string) => void }) {
  return (
    <div className="pointer-events-none fixed bottom-4 right-4 z-[100] flex w-full max-w-sm flex-col gap-2">
      {toasts.map((t) => (
        <Toast key={t.id} {...t} onDismiss={onDismiss} />
      ))}
    </div>
  );
}
