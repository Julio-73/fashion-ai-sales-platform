"use client";

import { Bell, ChevronLeft, Menu, Search } from "lucide-react";

import { t } from "@/lib/i18n";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const T = t.nav.topbar;

type TopbarProps = {
  isSidebarCollapsed: boolean;
  onToggleSidebar: () => void;
  onOpenMobileSidebar: () => void;
};

export function Topbar({ isSidebarCollapsed, onToggleSidebar, onOpenMobileSidebar }: TopbarProps) {
  return (
    <header className="sticky top-0 z-30 border-b bg-background/85 backdrop-blur-xl">
      <div className="flex h-16 items-center gap-3 px-4 sm:px-6 lg:px-8">
        <Button type="button" variant="ghost" size="icon" className="lg:hidden" onClick={onOpenMobileSidebar}>
          <Menu className="h-4 w-4" aria-hidden="true" />
          <span className="sr-only">{T.openNav}</span>
        </Button>
        <Button type="button" variant="ghost" size="icon" className="hidden lg:inline-flex" onClick={onToggleSidebar}>
          <ChevronLeft
            className={cn("h-4 w-4 transition-transform", isSidebarCollapsed && "rotate-180")}
            aria-hidden="true"
          />
          <span className="sr-only">{T.toggleNav}</span>
        </Button>

        <div className="relative hidden w-full max-w-md md:block">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <input
            className="h-10 w-full rounded-lg border bg-card pl-9 pr-3 text-sm outline-none transition focus-visible:ring-2 focus-visible:ring-ring"
            placeholder={T.searchPlaceholder}
            type="search"
          />
        </div>

        <div className="ml-auto flex items-center gap-2">
          <div className="hidden rounded-lg border bg-card px-3 py-2 text-xs text-muted-foreground sm:block">
            {T.demoCompany}
          </div>
          <Button type="button" variant="outline" size="icon">
            <Bell className="h-4 w-4" aria-hidden="true" />
            <span className="sr-only">{T.notifications}</span>
          </Button>
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-slate-900 text-xs font-semibold text-white">
            {T.avatarInitials}
          </div>
        </div>
      </div>
    </header>
  );
}

