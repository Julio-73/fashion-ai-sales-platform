"use client";

import { createContext, type ReactNode, useCallback, useContext, useEffect, useMemo, useState } from "react";

import * as authService from "@/services/auth.service";
import type { CurrentUser, LoginPayload } from "@/types/auth";

type AuthState = {
  accessToken: string | null;
  refreshToken: string | null;
  user: CurrentUser | null;
  isHydrated: boolean;
  isAuthenticated: boolean;
  login: (payload: LoginPayload) => Promise<void>;
  refreshSession: () => Promise<void>;
  logout: () => Promise<void>;
};

const storageKey = "ai-sales-agent-auth";

const AuthStoreContext = createContext<AuthState | null>(null);

type StoredAuth = {
  accessToken: string;
  refreshToken: string;
  user: CurrentUser;
};

export function AuthStoreProvider({ children }: { children: ReactNode }) {
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [refreshToken, setRefreshToken] = useState<string | null>(null);
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [isHydrated, setIsHydrated] = useState(false);

  useEffect(() => {
    const stored = window.localStorage.getItem(storageKey);
    if (stored) {
      try {
        const parsed = JSON.parse(stored) as StoredAuth;
        setAccessToken(parsed.accessToken);
        setRefreshToken(parsed.refreshToken);
        setUser(parsed.user);
      } catch {
        window.localStorage.removeItem(storageKey);
      }
    }
    setIsHydrated(true);
  }, []);

  const persistSession = useCallback((session: StoredAuth) => {
    setAccessToken(session.accessToken);
    setRefreshToken(session.refreshToken);
    setUser(session.user);
    window.localStorage.setItem(storageKey, JSON.stringify(session));
  }, []);

  const login = useCallback(
    async (payload: LoginPayload) => {
      const session = await authService.login(payload);
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

    const session = await authService.refreshToken({ refresh_token: refreshToken });

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
      await authService.logout({ refresh_token: token }).catch(() => undefined);
    }
  }, [refreshToken]);

  const value = useMemo<AuthState>(
    () => ({
      accessToken,
      refreshToken,
      user,
      isHydrated,
      isAuthenticated: Boolean(accessToken && refreshToken && user),
      login,
      refreshSession,
      logout
    }),
    [accessToken, refreshToken, user, isHydrated, login, refreshSession, logout]
  );

  return <AuthStoreContext.Provider value={value}>{children}</AuthStoreContext.Provider>;
}

export function useAuthStore() {
  const context = useContext(AuthStoreContext);
  if (!context) {
    throw new Error("useAuthStore must be used inside AuthStoreProvider");
  }
  return context;
}
