"use client";

import * as Dialog from "@radix-ui/react-dialog";
import { X } from "lucide-react";
import type { ReactNode } from "react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

type ModalProps = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  description?: string;
  children: ReactNode;
  size?: "sm" | "md" | "lg" | "xl" | "full";
  footer?: ReactNode;
};

const sizeMap = {
  sm: "max-w-sm",
  md: "max-w-lg",
  lg: "max-w-2xl",
  xl: "max-w-4xl",
  full: "max-w-[calc(100vw-2rem)]"
};

export function Modal({
  open,
  onOpenChange,
  title,
  description,
  children,
  size = "md",
  footer
}: ModalProps) {
  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-50 bg-slate-950/40 backdrop-blur-sm anim-fade-in" />
        <Dialog.Content
          className={cn(
            "fixed left-1/2 top-1/2 z-50 w-[calc(100%-2rem)] -translate-x-1/2 -translate-y-1/2 overflow-hidden rounded-xl border bg-card text-card-foreground shadow-2xl shadow-slate-950/20 focus:outline-none anim-scale-in",
            sizeMap[size]
          )}
        >
          <div className="flex items-start justify-between gap-4 border-b bg-gradient-to-b from-secondary/40 to-card px-6 py-4">
            <div className="min-w-0 flex-1">
              <Dialog.Title className="text-base font-semibold tracking-tight">
                {title}
              </Dialog.Title>
              {description ? (
                <Dialog.Description className="mt-1 text-sm leading-6 text-muted-foreground">
                  {description}
                </Dialog.Description>
              ) : null}
            </div>
            <Dialog.Close asChild>
              <Button type="button" variant="ghost" size="icon-sm" className="-mr-1 -mt-1">
                <X className="h-4 w-4" aria-hidden="true" />
                <span className="sr-only">Cerrar</span>
              </Button>
            </Dialog.Close>
          </div>
          <div className="px-6 py-5">{children}</div>
          {footer ? (
            <div className="flex items-center justify-end gap-2 border-t bg-secondary/30 px-6 py-3">
              {footer}
            </div>
          ) : null}
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
