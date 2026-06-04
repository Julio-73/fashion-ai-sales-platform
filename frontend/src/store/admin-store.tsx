"use client";

import {
  createContext,
  type ReactNode,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState
} from "react";

import * as adminService from "@/services/admin.service";
import type { AdminLoginPayload, AdminUser } from "@/types/admin";

type AdminState = {
  accessToken: string | null;
  refreshToken: string | null;
  user: AdminUser | null;
  isHydrated: boolean;
  isAuthenticated: boolean;
  isSuperAdmin: boolean;
  login: (payload: AdminLoginPayload) => Promise<void>;
  refreshSession: () => Promise<void>;
  logout: () => Promise<void>;
};

const storageKey = "ai-sales-agent-admin-auth";

const AdminStoreContext = createContext<AdminState | null>(null);

type StoredAdmin = {
  accessToken: string;
  refreshToken: string;
  user: AdminUser;
};

export function AdminStoreProvider({ children }: { children: ReactNode }) {
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [refreshToken, setRefreshToken] = useState<string | null>(null);
  const [user, setUser] = useState<AdminUser | null>(null);
  const [isHydrated, setIsHydrated] = useState(false);

  useEffect(() => {
    const stored = window.localStorage.getItem(storageKey);
    if (stored) {
      try {
        const parsed = JSON.parse(stored) as StoredAdmin;
        setAccessToken(parsed.accessToken);
        setRefreshToken(parsed.refreshToken);
        setUser(parsed.user);
      } catch {
        window.localStorage.removeItem(storageKey);
      }
    }
    setIsHydrated(true);
  }, []);

  const persistSession = useCallback((session: StoredAdmin) => {
    setAccessToken(session.accessToken);
    setRefreshToken(session.refreshToken);
    setUser(session.user);
    window.localStorage.setItem(storageKey, JSON.stringify(session));
  }, []);

  const login = useCallback(
    async (payload: AdminLoginPayload) => {
      const session = await adminService.adminLogin(payload);
      persistSession({
        accessToken: session.access_token,
        refreshToken: session.refresh_token,
        user: session.user
      });
    },
    [persistSession]
  );

  const refreshSession = useCallback(async () => {
    if (!refreshToken || !user) {
      return;
    }
    const session = await adminService.adminRefresh({ refresh_token: refreshToken });
    persistSession({
      accessToken: session.access_token,
      refreshToken: session.refresh_token,
      user
    });
  }, [persistSession, refreshToken, user]);

  const logout = useCallback(async () => {
    const token = refreshToken;
    setAccessToken(null);
    setRefreshToken(null);
    setUser(null);
    window.localStorage.removeItem(storageKey);
    if (token) {
      await adminService.adminLogout({ refresh_token: token }).catch(() => undefined);
    }
  }, [refreshToken]);

  const value = useMemo<AdminState>(
    () => ({
      accessToken,
      refreshToken,
      user,
      isHydrated,
      isAuthenticated: Boolean(accessToken && refreshToken && user),
      isSuperAdmin: user?.is_super_admin ?? false,
      login,
      refreshSession,
      logout
    }),
    [accessToken, refreshToken, user, isHydrated, login, refreshSession, logout]
  );

  return <AdminStoreContext.Provider value={value}>{children}</AdminStoreContext.Provider>;
}

export function useAdminStore() {
  const context = useContext(AdminStoreContext);
  if (!context) {
    throw new Error("useAdminStore must be used inside AdminStoreProvider");
  }
  return context;
}

export const ADMIN_STORAGE_KEY = storageKey;
