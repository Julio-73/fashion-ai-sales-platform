import { cn } from "@/lib/utils";

type StatusBadgeProps = {
  children: React.ReactNode;
  tone?:
    | "success"
    | "warning"
    | "neutral"
    | "info"
    | "destructive"
    | "primary"
    | "purple";
  className?: string;
  size?: "sm" | "md";
};

const toneClass = {
  success:
    "bg-success-50 text-success ring-success-200 dark:bg-success-50/20 dark:text-success-200 dark:ring-success-200/30",
  warning:
    "bg-warning-50 text-warning ring-warning-200 dark:bg-warning-50/20 dark:text-warning-200 dark:ring-warning-200/30",
  neutral: "bg-secondary text-secondary-foreground ring-border",
  info: "bg-info-50 text-info ring-info-100 dark:bg-info-50/20 dark:text-info-200 dark:ring-info-100/30",
  destructive:
    "bg-destructive-50 text-destructive ring-destructive-100 dark:bg-destructive-50/20 dark:text-destructive-100 dark:ring-destructive-100/30",
  primary:
    "bg-primary-50 text-primary-700 ring-primary-200 dark:bg-primary-50/20 dark:text-primary-300 dark:ring-primary-300/30",
  purple:
    "bg-purple/10 text-purple ring-purple/20 dark:text-purple dark:ring-purple/30"
};

const sizeClass = {
  sm: "text-[10px] px-1.5 py-0.5",
  md: "text-xs px-2 py-0.5"
};

export function StatusBadge({
  children,
  tone = "neutral",
  className,
  size = "md"
}: StatusBadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-md font-medium ring-1 ring-inset",
        toneClass[tone],
        sizeClass[size],
        className
      )}
    >
      {children}
    </span>
  );
}
