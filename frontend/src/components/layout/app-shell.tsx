"use client";

import { useState } from "react";

import { Sidebar } from "@/components/layout/sidebar";
import { Topbar } from "@/components/layout/topbar";
import { cn } from "@/lib/utils";

type AppShellProps = {
  children: React.ReactNode;
};

export function AppShell({ children }: AppShellProps) {
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);

  return (
    <div className="min-h-screen bg-background">
      <Sidebar
        isCollapsed={isSidebarCollapsed}
        isMobileOpen={isMobileSidebarOpen}
        onCloseMobile={() => setIsMobileSidebarOpen(false)}
      />
      <div
        className={cn(
          "min-h-screen transition-[padding] duration-300 ease-out",
          isSidebarCollapsed ? "lg:pl-[84px]" : "lg:pl-72"
        )}
      >
        <Topbar
          isSidebarCollapsed={isSidebarCollapsed}
          onToggleSidebar={() => setIsSidebarCollapsed((value) => !value)}
          onOpenMobileSidebar={() => setIsMobileSidebarOpen(true)}
        />
        <main className="px-4 pb-10 pt-5 sm:px-6 lg:px-8">{children}</main>
      </div>
    </div>
  );
}

