import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import * as React from "react";

import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "btn-base btn-press disabled:opacity-50 disabled:pointer-events-none",
  {
    variants: {
      variant: {
        default:
          "bg-primary text-primary-foreground shadow-sm hover:bg-primary-600 hover:shadow-md",
        secondary:
          "bg-secondary text-secondary-foreground border border-border/50 hover:bg-secondary/80",
        outline:
          "border border-border bg-card text-foreground shadow-sm hover:bg-secondary hover:border-primary-200",
        ghost: "text-foreground hover:bg-secondary",
        destructive:
          "bg-destructive text-destructive-foreground shadow-sm hover:bg-destructive/90",
        success:
          "bg-success text-success-foreground shadow-sm hover:bg-success/90",
        gradient:
          "bg-gradient-to-r from-primary to-purple text-primary-foreground shadow-sm hover:shadow-md hover:brightness-110",
        link: "text-primary underline-offset-4 hover:underline",
        glass:
          "glass-card border border-border/60 text-foreground shadow-sm hover:bg-card"
      },
      size: {
        default: "h-10 px-4 text-sm",
        sm: "h-8 px-3 text-xs",
        lg: "h-11 px-6 text-sm",
        icon: "h-10 w-10",
        "icon-sm": "h-8 w-8",
        "icon-xs": "h-7 w-7"
      }
    },
    defaultVariants: {
      variant: "default",
      size: "default"
    }
  }
);

export type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> &
  VariantProps<typeof buttonVariants> & {
    asChild?: boolean;
  };

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button";
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    );
  }
);
Button.displayName = "Button";

export { buttonVariants };
