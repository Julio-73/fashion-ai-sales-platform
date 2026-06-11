"use client";

import {
  Bell,
  ChevronDown,
  ChevronLeft,
  HelpCircle,
  Menu,
  Moon,
  Search,
  Sun
} from "lucide-react";

import { t } from "@/lib/i18n";
import { Avatar } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { KbdShortcut } from "@/components/ui/kbd";
import { useTheme } from "@/components/feedback/theme-provider";
import { cn } from "@/lib/utils";

const T = t.nav.topbar;

type TopbarProps = {
  isSidebarCollapsed: boolean;
  onToggleSidebar: () => void;
  onOpenMobileSidebar: () => void;
};

export function Topbar({
  isSidebarCollapsed,
  onToggleSidebar,
  onOpenMobileSidebar
}: TopbarProps) {
  const { theme, toggle } = useTheme();
  return (
    <header className="sticky top-0 z-30 border-b bg-background/80 backdrop-blur-xl supports-[backdrop-filter]:bg-background/60">
      <div className="flex h-16 items-center gap-3 px-4 sm:px-6 lg:px-8">
        <Button
          type="button"
          variant="ghost"
          size="icon-sm"
          className="lg:hidden"
          onClick={onOpenMobileSidebar}
          aria-label={T.openNav}
        >
          <Menu className="h-4 w-4" aria-hidden="true" />
        </Button>
        <Button
          type="button"
          variant="ghost"
          size="icon-sm"
          className="hidden lg:inline-flex"
          onClick={onToggleSidebar}
          aria-label={T.toggleNav}
        >
          <ChevronLeft
            className={cn(
              "h-4 w-4 transition-transform",
              isSidebarCollapsed && "rotate-180"
            )}
            aria-hidden="true"
          />
        </Button>

        <div className="relative hidden w-full max-w-md md:block">
          <Search
            className="pointer-events-none absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground"
            aria-hidden="true"
          />
          <input
            className="h-9 w-full rounded-md border bg-secondary/40 pl-9 pr-20 text-sm outline-none transition focus-visible:border-primary-200 focus-visible:bg-card focus-visible:ring-2 focus-visible:ring-ring"
            placeholder={T.searchPlaceholder}
            type="search"
            aria-label="Búsqueda global"
          />
          <div className="pointer-events-none absolute right-2 top-1/2 hidden -translate-y-1/2 sm:flex">
            <KbdShortcut keys={["⌘", "K"]} />
          </div>
        </div>

        <div className="ml-auto flex items-center gap-1.5">
          <Button
            type="button"
            variant="ghost"
            size="icon-sm"
            className="hidden md:inline-flex"
            aria-label="Ayuda"
            onClick={() => {
              const event = new KeyboardEvent("keydown", { key: "k", metaKey: true });
              document.dispatchEvent(event);
            }}
          >
            <HelpCircle className="h-4 w-4" aria-hidden="true" />
          </Button>
          <Button
            type="button"
            variant="ghost"
            size="icon-sm"
            onClick={toggle}
            aria-label={
              theme === "dark" ? "Cambiar a tema claro" : "Cambiar a tema oscuro"
            }
          >
            {theme === "dark" ? (
              <Sun className="h-4 w-4" aria-hidden="true" />
            ) : (
              <Moon className="h-4 w-4" aria-hidden="true" />
            )}
          </Button>
          <Button
            type="button"
            variant="ghost"
            size="icon-sm"
            className="relative"
            aria-label={T.notifications}
            disabled
          >
            <Bell className="h-4 w-4" aria-hidden="true" />
          </Button>
          <div className="ml-1 flex items-center gap-2 rounded-full border bg-card py-0.5 pl-0.5 pr-2.5">
            <Avatar name={T.avatarInitials} size="sm" />
            <div className="hidden flex-col leading-tight sm:flex">
              <span className="text-xs font-medium">{T.avatarInitials}</span>
              <span className="text-[10px] text-muted-foreground">
                {T.demoCompany}
              </span>
            </div>
            <ChevronDown
              className="hidden h-3.5 w-3.5 text-muted-foreground sm:block"
              aria-hidden="true"
            />
          </div>
        </div>
      </div>
    </header>
  );
}
