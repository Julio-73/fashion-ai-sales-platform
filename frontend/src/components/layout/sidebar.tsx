"use client";

import {
  BarChart3,
  Bot,
  Building2,
  MessageSquare,
  Package,
  Settings,
  Sparkles,
  UsersRound,
  Workflow
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { t } from "@/lib/i18n";
import { LogoutButton } from "@/components/auth/logout-button";
import { cn } from "@/lib/utils";

const S = t.nav.sidebar;

const navGroups = [
  {
    label: S.workspace,
    items: [
      { label: S.customers, icon: UsersRound, href: "/dashboard/customers" },
      { label: S.products, icon: Package, href: "/dashboard/products" },
      { label: S.chats, icon: MessageSquare, href: "/dashboard/conversations" },
      { label: S.analytics, icon: BarChart3, href: "/dashboard" },
      { label: S.automations, icon: Workflow, href: "/dashboard" }
    ]
  },
  {
    label: S.platform,
    items: [
      { label: S.aiSales, icon: Bot, href: "/dashboard/ai-sales" },
      { label: S.settings, icon: Settings, href: "/dashboard" }
    ]
  }
];

type SidebarProps = {
  isCollapsed: boolean;
  isMobileOpen: boolean;
  onCloseMobile: () => void;
};

export function Sidebar({ isCollapsed, isMobileOpen, onCloseMobile }: SidebarProps) {
  const pathname = usePathname();

  return (
    <>
      <button
        type="button"
        aria-label={S.closeNav}
        className={cn(
          "fixed inset-0 z-40 bg-slate-950/30 backdrop-blur-sm transition-opacity lg:hidden",
          isMobileOpen ? "opacity-100" : "pointer-events-none opacity-0"
        )}
        onClick={onCloseMobile}
      />
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-50 flex w-72 flex-col border-r bg-card/95 shadow-2xl shadow-slate-950/10 backdrop-blur-xl transition-transform duration-300 ease-out lg:translate-x-0 lg:shadow-none",
          isMobileOpen ? "translate-x-0" : "-translate-x-full",
          isCollapsed && "lg:w-[84px]"
        )}
      >
        <div className="flex h-16 items-center gap-3 border-b px-4">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary text-primary-foreground shadow-sm">
            <Building2 className="h-5 w-5" aria-hidden="true" />
          </div>
          <div className={cn("min-w-0 transition-opacity", isCollapsed && "lg:hidden")}>
            <p className="truncate text-sm font-semibold">{S.brand}</p>
            <p className="truncate text-xs text-muted-foreground">{S.subtitle}</p>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto px-3 py-4">
          {navGroups.map((group) => (
            <div key={group.label} className="mb-5">
              <p
                className={cn(
                  "mb-2 px-2 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground",
                  isCollapsed && "lg:sr-only"
                )}
              >
                {group.label}
              </p>
              <nav className="grid gap-1">
                {group.items.map((item) => {
                  const isActive = pathname === item.href;
                  return (
                    <Link
                      key={item.label}
                      href={item.href}
                      className={cn(
                        "group flex h-10 items-center gap-3 rounded-lg px-3 text-sm font-medium text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                        isActive && "bg-secondary text-foreground shadow-sm",
                        isCollapsed && "lg:justify-center lg:px-0"
                      )}
                    >
                      <item.icon className="h-4 w-4 shrink-0" aria-hidden="true" />
                      <span className={cn("truncate", isCollapsed && "lg:hidden")}>{item.label}</span>
                    </Link>
                  );
                })}
              </nav>
            </div>
          ))}
        </div>

        <div className="border-t p-3">
          <div
            className={cn(
              "mb-3 rounded-lg border bg-background p-3",
              isCollapsed && "lg:flex lg:justify-center lg:p-2"
            )}
          >
            <Sparkles className="h-4 w-4 text-accent" aria-hidden="true" />
            <div className={cn("mt-2", isCollapsed && "lg:hidden")}>
              <p className="text-xs font-semibold">{S.foundationLabel}</p>
              <p className="mt-1 text-xs leading-5 text-muted-foreground">{S.foundationDesc}</p>
            </div>
          </div>
          <LogoutButton isCollapsed={isCollapsed} />
        </div>
      </aside>
    </>
  );
}
