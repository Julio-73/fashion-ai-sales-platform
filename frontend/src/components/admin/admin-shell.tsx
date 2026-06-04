"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import type { ReactNode } from "react";

import { t } from "@/lib/i18n";
import { Button } from "@/components/ui/button";
import { useAdminStore } from "@/store/admin-store";

type AdminShellProps = {
  children: ReactNode;
};

type NavItem = {
  href: string;
  label: string;
};

export function AdminShell({ children }: AdminShellProps) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout } = useAdminStore();
  const L = t.admin.nav;

  const items: NavItem[] = [
    { href: "/admin", label: L.dashboard },
    { href: "/admin/tenants", label: L.tenants },
    { href: "/admin/audit", label: L.audit }
  ];

  const handleLogout = async () => {
    await logout();
    router.replace("/admin/login");
  };

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b bg-card">
        <div className="mx-auto flex max-w-7xl flex-col gap-3 px-4 py-4 sm:flex-row sm:items-center sm:justify-between sm:px-6 lg:px-8">
          <div>
            <p className="text-sm font-semibold text-foreground">{L.brand}</p>
            <p className="text-xs text-muted-foreground">{L.subtitle}</p>
          </div>
          {user ? (
            <div className="flex flex-col items-end gap-1 text-xs text-muted-foreground sm:flex-row sm:items-center sm:gap-3">
              <span>
                {L.signedInAs.replace("{email}", user.email)}
                {user.is_super_admin ? " · super_admin" : ` · ${user.rol}`}
              </span>
              <Button type="button" variant="outline" size="sm" onClick={handleLogout}>
                {L.logout}
              </Button>
            </div>
          ) : null}
        </div>
        <nav className="mx-auto flex max-w-7xl gap-1 overflow-x-auto px-4 pb-3 sm:px-6 lg:px-8">
          {items.map((item) => {
            const active =
              item.href === "/admin"
                ? pathname === "/admin"
                : pathname?.startsWith(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={
                  "rounded-md px-3 py-1.5 text-sm font-medium transition-colors " +
                  (active
                    ? "bg-primary text-primary-foreground"
                    : "text-muted-foreground hover:bg-secondary hover:text-foreground")
                }
              >
                {item.label}
              </Link>
            );
          })}
        </nav>
      </header>
      <main className="mx-auto max-w-7xl px-4 pb-10 pt-6 sm:px-6 lg:px-8">{children}</main>
    </div>
  );
}
