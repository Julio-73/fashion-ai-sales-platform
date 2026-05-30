"use client";

import { useRouter } from "next/navigation";
import type { ReactNode } from "react";
import { useEffect } from "react";

import { t } from "@/lib/i18n";
import { useAuthStore } from "@/store/auth-store";

const STORAGE_KEY = "ai-sales-agent-auth";

export function ProtectedRoute({ children }: { children: ReactNode }) {
  const router = useRouter();
  const { isAuthenticated, isHydrated } = useAuthStore();

  useEffect(() => {
    if (isHydrated && !isAuthenticated) {
      const stored = window.localStorage.getItem(STORAGE_KEY);
      if (stored) {
        try {
          const parsed = JSON.parse(stored);
          if (parsed.accessToken && parsed.refreshToken && parsed.user) {
            return;
          }
        } catch {
          window.localStorage.removeItem(STORAGE_KEY);
        }
      }
      router.replace("/login");
    }
  }, [isAuthenticated, isHydrated, router]);

  if (!isHydrated) {
    const stored = typeof window !== "undefined" ? window.localStorage.getItem(STORAGE_KEY) : null;
    if (stored) {
      try {
        const parsed = JSON.parse(stored);
        if (parsed.accessToken && parsed.refreshToken && parsed.user) {
          return <>{children}</>;
        }
      } catch {
        window.localStorage.removeItem(STORAGE_KEY);
      }
    }
    return (
      <div className="flex min-h-screen items-center justify-center bg-background px-4">
        <div className="rounded-lg border bg-card px-5 py-4 text-sm text-muted-foreground shadow-sm">
          {t.auth.protected.loading}
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background px-4">
        <div className="rounded-lg border bg-card px-5 py-4 text-sm text-muted-foreground shadow-sm">
          {t.auth.protected.loading}
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
