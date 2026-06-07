"use client";

import { useEffect, useMemo, useState } from "react";
import {
  BarChart3,
  Bot,
  Calendar,
  CheckCircle2,
  Command,
  Inbox,
  ListChecks,
  MessageSquare,
  Package,
  PieChart,
  Search,
  Settings,
  ShoppingBag,
  UsersRound,
  type LucideIcon
} from "lucide-react";
import { useRouter } from "next/navigation";
import { AnimatePresence, motion } from "framer-motion";

import { Kbd } from "@/components/ui/kbd";
import { cn } from "@/lib/utils";
import { t } from "@/lib/i18n";

const NAV = t.nav.sidebar;

type QuickAction = {
  key: string;
  label: string;
  description?: string;
  icon: LucideIcon;
  href: string;
  group: "Navegación" | "Búsqueda rápida" | "Acciones";
};

const actions: QuickAction[] = [
  { key: "home", label: "Workspace", icon: BarChart3, href: "/dashboard", group: "Navegación" },
  { key: "executive", label: "Executive Dashboard", icon: PieChart, href: "/dashboard/executive", group: "Navegación" },
  { key: "pipeline", label: "Pipeline", icon: ListChecks, href: "/dashboard/pipeline", group: "Navegación" },
  { key: "crm", label: "CRM 360", icon: UsersRound, href: "/dashboard/customers", group: "Navegación" },
  { key: "conversations", label: "Conversaciones", icon: MessageSquare, href: "/dashboard/conversations", group: "Navegación" },
  { key: "orders", label: "Pedidos", icon: ShoppingBag, href: "/dashboard/orders", group: "Navegación" },
  { key: "inventory", label: "Inventario", icon: Package, href: "/dashboard/inventory", group: "Navegación" },
  { key: "tasks", label: "Task Center", icon: CheckCircle2, href: "/dashboard/tasks", group: "Navegación" },
  { key: "automations", label: "Automatizaciones", icon: Settings, href: "/dashboard/automations", group: "Navegación" },
  { key: "alerts", label: "Alert Center", icon: Inbox, href: "/dashboard/alerts", group: "Navegación" },
  { key: "calendar", label: "Calendario", icon: Calendar, href: "/dashboard/calendar", group: "Navegación" },
  { key: "reports", label: "Reportes", icon: BarChart3, href: "/dashboard/reports", group: "Navegación" },
  { key: "ai-live", label: "AI Live", icon: Bot, href: "/dashboard/ai-sales", group: "Navegación" }
];

export function CommandPalette() {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");

  useEffect(() => {
    function handleKey(e: KeyboardEvent) {
      const isMod = e.metaKey || e.ctrlKey;
      if (isMod && (e.key === "k" || e.key === "K")) {
        e.preventDefault();
        setOpen((v) => !v);
      }
      if (e.key === "Escape" && open) {
        e.preventDefault();
        setOpen(false);
      }
    }
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [open]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return actions;
    return actions.filter(
      (a) =>
        a.label.toLowerCase().includes(q) ||
        a.description?.toLowerCase().includes(q) ||
        a.href.toLowerCase().includes(q)
    );
  }, [query]);

  const grouped = useMemo(() => {
    const out: Record<string, QuickAction[]> = {};
    filtered.forEach((a) => {
      if (!out[a.group]) out[a.group] = [];
      out[a.group].push(a);
    });
    return out;
  }, [filtered]);

  function go(href: string) {
    setOpen(false);
    setQuery("");
    router.push(href);
  }

  return (
    <AnimatePresence>
      {open ? (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.12 }}
          className="fixed inset-0 z-50 flex items-start justify-center bg-foreground/30 px-4 pt-24 backdrop-blur-sm"
          onClick={() => setOpen(false)}
          role="dialog"
          aria-modal="true"
          aria-label="Búsqueda global"
        >
          <motion.div
            initial={{ opacity: 0, y: -8, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -8, scale: 0.98 }}
            transition={{ duration: 0.16 }}
            onClick={(e) => e.stopPropagation()}
            className="w-full max-w-2xl overflow-hidden rounded-2xl border border-border bg-card shadow-2xl"
          >
            <div className="flex items-center gap-3 border-b border-border px-4 py-3">
              <Search
                className="h-4 w-4 shrink-0 text-muted-foreground"
                aria-hidden="true"
              />
              <input
                autoFocus
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Buscar en el workspace, ir a módulo o ejecutar acción…"
                className="flex-1 bg-transparent text-sm outline-none placeholder:text-muted-foreground"
                aria-label="Buscar"
              />
              <Kbd>
                <span className="inline-flex items-center gap-0.5">
                  <Command className="h-3 w-3" aria-hidden="true" /> K
                </span>
              </Kbd>
            </div>
            <div className="max-h-[60vh] overflow-y-auto p-2">
              {Object.keys(grouped).length === 0 ? (
                <p className="px-3 py-8 text-center text-sm text-muted-foreground">
                  Sin coincidencias para “{query}”.
                </p>
              ) : (
                Object.entries(grouped).map(([group, items]) => (
                  <div key={group} className="mb-2">
                    <p className="px-2 pb-1 pt-2 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
                      {group}
                    </p>
                    <ul className="grid gap-0.5">
                      {items.map((a) => {
                        const Icon = a.icon;
                        return (
                          <li key={a.key}>
                            <button
                              type="button"
                              onClick={() => go(a.href)}
                              className={cn(
                                "group flex w-full items-center gap-3 rounded-lg px-2.5 py-2 text-left text-sm transition",
                                "hover:bg-muted focus-visible:bg-muted focus-visible:outline-none"
                              )}
                            >
                              <span
                                className={cn(
                                  "flex h-8 w-8 items-center justify-center rounded-md bg-secondary text-muted-foreground transition",
                                  "group-hover:bg-primary-50 group-hover:text-primary"
                                )}
                              >
                                <Icon className="h-4 w-4" aria-hidden="true" />
                              </span>
                              <span className="min-w-0 flex-1">
                                <span className="block truncate font-medium text-foreground">
                                  {a.label}
                                </span>
                                {a.description ? (
                                  <span className="block truncate text-xs text-muted-foreground">
                                    {a.description}
                                  </span>
                                ) : null}
                              </span>
                              <span className="text-[10px] text-muted-foreground">
                                {a.href}
                              </span>
                            </button>
                          </li>
                        );
                      })}
                    </ul>
                  </div>
                ))
              )}
            </div>
            <div className="flex items-center justify-between border-t border-border bg-muted/30 px-3 py-2 text-[10px] text-muted-foreground">
              <span>{NAV.brand}</span>
              <span className="inline-flex items-center gap-2">
                <Kbd>Esc</Kbd> cerrar
              </span>
            </div>
          </motion.div>
        </motion.div>
      ) : null}
    </AnimatePresence>
  );
}
