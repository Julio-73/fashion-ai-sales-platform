"use client";

import { useRouter } from "next/navigation";
import type { ReactNode } from "react";
import { useEffect } from "react";

import { t } from "@/lib/i18n";
import { ADMIN_STORAGE_KEY, useAdminStore } from "@/store/admin-store";

type Props = {
  children: ReactNode;
  /** When true the route also requires ``super_admin`` role. */
  requireSuperAdmin?: boolean;
};

export function AdminProtectedRoute({ children, requireSuperAdmin = false }: Props) {
  const router = useRouter();
  const { isAuthenticated, isHydrated, isSuperAdmin } = useAdminStore();

  useEffect(() => {
    if (!isHydrated) {
      return;
    }
    if (!isAuthenticated) {
      router.replace("/admin/login");
      return;
    }
    if (requireSuperAdmin && !isSuperAdmin) {
      router.replace("/admin");
    }
  }, [isAuthenticated, isHydrated, isSuperAdmin, requireSuperAdmin, router]);

  if (!isHydrated || !isAuthenticated) {
    if (typeof window !== "undefined") {
      const stored = window.localStorage.getItem(ADMIN_STORAGE_KEY);
      if (stored) {
        try {
          const parsed = JSON.parse(stored);
          if (parsed.accessToken && parsed.refreshToken && parsed.user) {
            return <>{children}</>;
          }
        } catch {
          window.localStorage.removeItem(ADMIN_STORAGE_KEY);
        }
      }
    }
    return (
      <div className="flex min-h-screen items-center justify-center bg-background px-4">
        <div className="rounded-lg border bg-card px-5 py-4 text-sm text-muted-foreground shadow-sm">
          {t.admin.protected.loading}
        </div>
      </div>
    );
  }

  if (requireSuperAdmin && !isSuperAdmin) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background px-4">
        <div className="max-w-md rounded-lg border bg-card p-6 text-center shadow-sm">
          <h1 className="text-lg font-semibold text-card-foreground">
            {t.admin.protected.forbiddenTitle}
          </h1>
          <p className="mt-2 text-sm text-muted-foreground">
            {t.admin.protected.forbiddenDesc}
          </p>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
