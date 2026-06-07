import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

type DashboardContentProps = {
  children: ReactNode;
  className?: string;
  size?: "default" | "wide" | "narrow";
};

const sizeMap = {
  default: "max-w-7xl",
  wide: "max-w-[1500px]",
  narrow: "max-w-5xl"
};

export function DashboardContent({
  children,
  className,
  size = "default"
}: DashboardContentProps) {
  return (
    <div
      className={cn(
        "mx-auto grid w-full gap-6",
        sizeMap[size],
        className
      )}
    >
      {children}
    </div>
  );
}
