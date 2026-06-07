"use client";

import { useState } from "react";

import { Sidebar } from "@/components/layout/sidebar";
import { Topbar } from "@/components/layout/topbar";
import { Toaster, useToasts } from "@/components/feedback/toast";
import { CommandPalette } from "@/components/feedback/command-palette";
import { ThemeProvider } from "@/components/feedback/theme-provider";
import { cn } from "@/lib/utils";

type AppShellProps = {
  children: React.ReactNode;
};

export function AppShell({ children }: AppShellProps) {
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);
  const toasts = useToasts();

  return (
    <ThemeProvider>
      <div className="relative min-h-screen bg-background">
        <div
          aria-hidden="true"
          className="pointer-events-none fixed inset-0 -z-10 bg-[radial-gradient(ellipse_at_top,hsl(var(--primary)/0.05),transparent_60%)]"
        />
        <Sidebar
          isCollapsed={isSidebarCollapsed}
          isMobileOpen={isMobileSidebarOpen}
          onCloseMobile={() => setIsMobileSidebarOpen(false)}
        />
        <div
          className={cn(
            "min-h-screen transition-[padding] duration-300 ease-out-expo",
            isSidebarCollapsed ? "lg:pl-[84px]" : "lg:pl-72"
          )}
        >
          <Topbar
            isSidebarCollapsed={isSidebarCollapsed}
            onToggleSidebar={() => setIsSidebarCollapsed((value) => !value)}
            onOpenMobileSidebar={() => setIsMobileSidebarOpen(true)}
          />
          <main className="px-4 pb-12 pt-5 sm:px-6 lg:px-8">{children}</main>
        </div>
        <Toaster toasts={toasts.toasts} onDismiss={toasts.dismiss} />
        <CommandPalette />
      </div>
    </ThemeProvider>
  );
}
