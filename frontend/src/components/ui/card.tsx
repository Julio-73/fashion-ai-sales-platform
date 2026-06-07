import * as React from "react";

import { cn } from "@/lib/utils";

export const Card = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement> & {
    variant?: "default" | "elevated" | "glow" | "outline" | "glass";
    interactive?: boolean;
    padding?: "none" | "sm" | "md" | "lg";
  }
>(({ className, variant = "default", interactive, padding, ...props }, ref) => {
  const paddingMap = {
    none: "",
    sm: "p-4",
    md: "p-5",
    lg: "p-6"
  };

  const variantMap = {
    default: "card-surface",
    elevated: "card-elevated",
    glow: "card-glow",
    outline: "rounded-xl border bg-card",
    glass: "rounded-xl border glass-card shadow-sm"
  };

  return (
    <div
      ref={ref}
      className={cn(
        variantMap[variant],
        interactive && "card-surface-interactive",
        padding && paddingMap[padding],
        className
      )}
      {...props}
    />
  );
});
Card.displayName = "Card";

export function CardHeader({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("flex flex-col gap-1.5 px-5 pt-5", className)}
      {...props}
    />
  );
}

export function CardTitle({
  className,
  ...props
}: React.HTMLAttributes<HTMLHeadingElement>) {
  return (
    <h3
      className={cn(
        "text-sm font-semibold tracking-tight text-foreground",
        className
      )}
      {...props}
    />
  );
}

export function CardDescription({
  className,
  ...props
}: React.HTMLAttributes<HTMLParagraphElement>) {
  return (
    <p
      className={cn("text-xs leading-5 text-muted-foreground", className)}
      {...props}
    />
  );
}

export function CardContent({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("px-5 pb-5 pt-4", className)} {...props} />;
}

export function CardFooter({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "flex items-center justify-between border-t px-5 py-3",
        className
      )}
      {...props}
    />
  );
}
