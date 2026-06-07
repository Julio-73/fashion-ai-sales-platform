"use client";

import { motion } from "framer-motion";
import {
  AlertTriangle,
  BarChart3,
  Bot,
  Building2,
  Calendar,
  ClipboardList,
  LineChart,
  ListChecks,
  MessageSquare,
  Package,
  Settings,
  Sparkles,
  UsersRound,
  Workflow,
  type LucideIcon
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { t } from "@/lib/i18n";
import { LogoutButton } from "@/components/auth/logout-button";
import { cn } from "@/lib/utils";

const S = t.nav.sidebar;

type NavItem = {
  label: string;
  icon: LucideIcon;
  href: string;
  badge?: string;
  highlight?: boolean;
};

type NavGroup = {
  label: string;
  items: NavItem[];
};

const navGroups: NavGroup[] = [
  {
    label: S.workspace,
    items: [
      {
        label: "Dashboard Ejecutivo",
        icon: LineChart,
        href: "/dashboard/executive",
        highlight: true
      },
      { label: S.customers, icon: UsersRound, href: "/dashboard/customers" },
      { label: S.products, icon: Package, href: "/dashboard/products" },
      { label: S.chats, icon: MessageSquare, href: "/dashboard/conversations" },
      { label: "Pedidos", icon: ClipboardList, href: "/dashboard/orders" },
      { label: S.analytics, icon: BarChart3, href: "/dashboard" },
      { label: "Task Center", icon: ListChecks, href: "/dashboard/tasks" },
      { label: "Calendario", icon: Calendar, href: "/dashboard/calendar" },
      { label: "Alertas", icon: AlertTriangle, href: "/dashboard/alerts" },
      { label: S.automations, icon: Workflow, href: "/dashboard/automations" }
    ]
  },
  {
    label: S.platform,
    items: [
      { label: S.aiSales, icon: Bot, href: "/dashboard/ai-sales" },

    ]
  }
];

type SidebarProps = {
  isCollapsed: boolean;
  isMobileOpen: boolean;
  onCloseMobile: () => void;
};

export function Sidebar({
  isCollapsed,
  isMobileOpen,
  onCloseMobile
}: SidebarProps) {
  const pathname = usePathname();

  return (
    <>
      <button
        type="button"
        aria-label={S.closeNav}
        className={cn(
          "fixed inset-0 z-40 bg-slate-950/40 backdrop-blur-sm transition-opacity lg:hidden",
          isMobileOpen ? "opacity-100" : "pointer-events-none opacity-0"
        )}
        onClick={onCloseMobile}
      />
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-50 flex w-72 flex-col border-r bg-card/95 shadow-xl shadow-slate-950/[0.04] backdrop-blur-2xl transition-[width,transform] duration-300 ease-out-expo lg:translate-x-0",
          isMobileOpen ? "translate-x-0" : "-translate-x-full",
          isCollapsed && "lg:w-[84px]"
        )}
      >
        <div className="flex h-16 items-center gap-3 border-b px-4">
          <div className="relative flex h-9 w-9 shrink-0 items-center justify-center overflow-hidden rounded-lg brand-gradient shadow-glow">
            <Building2
              className="h-4 w-4 text-white drop-shadow"
              aria-hidden="true"
            />
          </div>
          <div
            className={cn(
              "min-w-0 transition-opacity",
              isCollapsed && "lg:hidden"
            )}
          >
            <p className="truncate text-sm font-semibold tracking-tight">
              {S.brand}
            </p>
            <p className="truncate text-[11px] text-muted-foreground">
              {S.subtitle}
            </p>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto px-3 py-4 scrollbar-hide">
          {navGroups.map((group, groupIdx) => (
            <div key={group.label} className={cn(groupIdx > 0 && "mt-5")}>
              <p
                className={cn(
                  "mb-1.5 px-2 text-[10px] font-semibold uppercase tracking-[0.14em] text-muted-foreground",
                  isCollapsed && "lg:sr-only"
                )}
              >
                {group.label}
              </p>
              <nav className="grid gap-0.5">
                {group.items.map((item) => {
                  const isActive =
                    pathname === item.href ||
                    (item.href !== "/dashboard" &&
                      pathname.startsWith(item.href + "/"));
                  return (
                    <Link
                      key={item.label}
                      href={item.href}
                      className={cn(
                        "group relative flex h-9 items-center gap-3 rounded-md px-3 text-sm font-medium transition-all",
                        isCollapsed && "lg:justify-center lg:px-0",
                        isActive
                          ? "text-foreground"
                          : "text-muted-foreground hover:bg-secondary/60 hover:text-foreground"
                      )}
                    >
                      {isActive ? (
                        <motion.span
                          layoutId="sidebar-active"
                          className="absolute inset-0 rounded-md bg-secondary shadow-[inset_0_0_0_1px_hsl(var(--border))]"
                          transition={{
                            type: "spring",
                            stiffness: 380,
                            damping: 30
                          }}
                        />
                      ) : null}
                      <item.icon
                        className={cn(
                          "relative h-4 w-4 shrink-0 transition-colors",
                          isActive ? "text-primary" : "text-muted-foreground",
                          item.highlight && !isActive && "text-purple"
                        )}
                        aria-hidden="true"
                      />
                      <span
                        className={cn(
                          "relative truncate",
                          isCollapsed && "lg:hidden"
                        )}
                      >
                        {item.label}
                      </span>
                      {item.badge ? (
                        <span
                          className={cn(
                            "relative ml-auto rounded-md bg-primary-50 px-1.5 py-0.5 text-[10px] font-semibold text-primary-700 dark:bg-primary-50/20 dark:text-primary-300",
                            isCollapsed && "lg:hidden"
                          )}
                        >
                          {item.badge}
                        </span>
                      ) : null}
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
              "mb-3 rounded-lg border bg-gradient-to-br from-primary-50/60 to-purple/5 p-3",
              isCollapsed && "lg:flex lg:justify-center lg:p-2"
            )}
          >
            <Sparkles
              className="h-4 w-4 text-purple"
              aria-hidden="true"
            />
            <div
              className={cn("mt-2", isCollapsed && "lg:hidden")}
            >
              <p className="text-xs font-semibold">{S.foundationLabel}</p>
              <p className="mt-1 text-[11px] leading-5 text-muted-foreground">
                {S.foundationDesc}
              </p>
            </div>
          </div>
          <LogoutButton isCollapsed={isCollapsed} />
        </div>
      </aside>
    </>
  );
}
