import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

type DashboardContentProps = {
  children: ReactNode;
  className?: string;
};

export function DashboardContent({ children, className }: DashboardContentProps) {
  return <div className={cn("mx-auto grid w-full max-w-7xl gap-6", className)}>{children}</div>;
}

