import { cn } from "@/lib/utils";

type AvatarProps = {
  name: string;
  src?: string | null;
  size?: "xs" | "sm" | "md" | "lg" | "xl";
  className?: string;
  status?: "online" | "offline" | "busy" | "away";
  ring?: boolean;
};

const sizeMap = {
  xs: "h-6 w-6 text-[10px]",
  sm: "h-7 w-7 text-[11px]",
  md: "h-9 w-9 text-xs",
  lg: "h-11 w-11 text-sm",
  xl: "h-14 w-14 text-base"
};

function getInitials(name: string): string {
  const parts = name.trim().split(/\s+/);
  if (parts.length === 0) return "?";
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

function getColorFromName(name: string): string {
  let hash = 0;
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash);
  }
  const colors = [
    "bg-blue-100 text-blue-700 dark:bg-blue-950 dark:text-blue-300",
    "bg-purple-100 text-purple-700 dark:bg-purple-950 dark:text-purple-300",
    "bg-pink-100 text-pink-700 dark:bg-pink-950 dark:text-pink-300",
    "bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300",
    "bg-amber-100 text-amber-700 dark:bg-amber-950 dark:text-amber-300",
    "bg-rose-100 text-rose-700 dark:bg-rose-950 dark:text-rose-300",
    "bg-cyan-100 text-cyan-700 dark:bg-cyan-950 dark:text-cyan-300",
    "bg-indigo-100 text-indigo-700 dark:bg-indigo-950 dark:text-indigo-300"
  ];
  return colors[Math.abs(hash) % colors.length];
}

const statusColorMap = {
  online: "bg-emerald-500",
  offline: "bg-slate-400",
  busy: "bg-rose-500",
  away: "bg-amber-500"
};

export function Avatar({
  name,
  src,
  size = "md",
  className,
  status,
  ring
}: AvatarProps) {
  return (
    <span
      className={cn(
        "relative inline-flex shrink-0 items-center justify-center overflow-hidden rounded-full font-semibold uppercase",
        sizeMap[size],
        ring && "ring-2 ring-background",
        !src && getColorFromName(name),
        className
      )}
      aria-label={name}
      title={name}
    >
      {src ? (
        <img
          src={src}
          alt={name}
          className="h-full w-full object-cover"
          loading="lazy"
        />
      ) : (
        <span>{getInitials(name)}</span>
      )}
      {status ? (
        <span
          aria-hidden="true"
          className={cn(
            "absolute bottom-0 right-0 h-2.5 w-2.5 rounded-full ring-2 ring-background",
            statusColorMap[status]
          )}
        />
      ) : null}
    </span>
  );
}

type AvatarStackProps = {
  names: string[];
  max?: number;
  size?: "xs" | "sm" | "md" | "lg";
};

export function AvatarStack({ names, max = 3, size = "sm" }: AvatarStackProps) {
  const shown = names.slice(0, max);
  const remaining = Math.max(0, names.length - max);
  return (
    <div className="flex -space-x-2">
      {shown.map((n) => (
        <Avatar key={n} name={n} size={size} ring />
      ))}
      {remaining > 0 ? (
        <span
          className={cn(
            "relative inline-flex shrink-0 items-center justify-center rounded-full bg-secondary font-semibold text-muted-foreground ring-2 ring-background",
            sizeMap[size]
          )}
        >
          +{remaining}
        </span>
      ) : null}
    </div>
  );
}
