import { cn } from "@/lib/utils";

type SkeletonProps = React.HTMLAttributes<HTMLDivElement> & {
  className?: string;
  variant?: "shimmer" | "pulse";
};

export function Skeleton({
  className,
  variant = "shimmer",
  ...props
}: SkeletonProps) {
  return (
    <div
      role="status"
      aria-label="Cargando"
      className={cn(
        "rounded-md",
        variant === "shimmer"
          ? "skeleton-shimmer"
          : "animate-pulse bg-muted",
        className
      )}
      {...props}
    />
  );
}

type SkeletonTextProps = {
  lines?: number;
  className?: string;
  lastLineWidth?: string;
};

export function SkeletonText({
  lines = 3,
  className,
  lastLineWidth = "60%"
}: SkeletonTextProps) {
  return (
    <div
      className={cn("space-y-2", className)}
      role="status"
      aria-label="Cargando"
    >
      {Array.from({ length: lines }).map((_, idx) => (
        <Skeleton
          key={idx}
          className={cn(
            "h-3",
            idx === lines - 1 ? "w-[var(--skel-last-w)]" : "w-full"
          )}
          style={{ ["--skel-last-w" as string]: lastLineWidth }}
        />
      ))}
    </div>
  );
}

export function MetricCardSkeleton() {
  return (
    <div className="card-surface p-5">
      <div className="flex items-center justify-between">
        <Skeleton className="h-3 w-24" />
        <Skeleton className="h-9 w-9 rounded-lg" />
      </div>
      <Skeleton className="mt-5 h-7 w-32" />
      <Skeleton className="mt-4 h-3 w-20" />
    </div>
  );
}

export function DashboardSkeleton({ count = 4 }: { count?: number }) {
  return (
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      {Array.from({ length: count }).map((_, i) => (
        <MetricCardSkeleton key={i} />
      ))}
    </div>
  );
}

export function TableSkeleton({
  rows = 6,
  cols = 4
}: {
  rows?: number;
  cols?: number;
}) {
  return (
    <div className="card-surface overflow-hidden">
      <div className="border-b bg-secondary/30 px-4 py-3">
        <div className="flex gap-4">
          {Array.from({ length: cols }).map((_, i) => (
            <Skeleton key={i} className="h-3 flex-1" />
          ))}
        </div>
      </div>
      <div className="divide-y">
        {Array.from({ length: rows }).map((_, rowIdx) => (
          <div key={rowIdx} className="flex items-center gap-4 px-4 py-3.5">
            {Array.from({ length: cols }).map((_, colIdx) => (
              <Skeleton
                key={colIdx}
                className="h-3 flex-1"
                style={{ maxWidth: `${100 - colIdx * 15}%` }}
              />
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}

export function ChartSkeleton({ height = 240 }: { height?: number }) {
  const heights = [40, 60, 35, 75, 55, 80, 45, 70, 50, 90, 65, 85];
  return (
    <div className="card-surface p-5">
      <div className="flex items-center justify-between">
        <Skeleton className="h-4 w-32" />
        <Skeleton className="h-7 w-24 rounded-md" />
      </div>
      <div className="mt-6 flex items-end gap-2" style={{ height }}>
        {Array.from({ length: 12 }).map((_, i) => (
          <Skeleton
            key={i}
            className="flex-1 rounded-md"
            style={{ height: `${heights[i]}%` }}
          />
        ))}
      </div>
    </div>
  );
}

export function ListSkeleton({ rows = 4 }: { rows?: number }) {
  return (
    <div className="card-surface divide-y">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="flex items-center gap-3 px-4 py-3.5">
          <Skeleton className="h-9 w-9 rounded-full" />
          <div className="flex-1 space-y-2">
            <Skeleton className="h-3 w-3/4" />
            <Skeleton className="h-2.5 w-1/2" />
          </div>
          <Skeleton className="h-6 w-16 rounded-md" />
        </div>
      ))}
    </div>
  );
}
