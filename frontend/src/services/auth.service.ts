import type { AuthSession, CurrentUser, LoginPayload, RefreshTokenPayload, TokenResponse } from "@/types/auth";
import { apiGet, apiPost } from "@/services/api-client";

export function getCurrentUser(accessToken: string): Promise<CurrentUser> {
  return apiGet<CurrentUser>("/auth/me", { accessToken });
}

export function login(payload: LoginPayload): Promise<AuthSession> {
  return apiPost<AuthSession, LoginPayload>("/auth/login", payload);
}

export function refreshToken(payload: RefreshTokenPayload): Promise<TokenResponse> {
  return apiPost<TokenResponse, RefreshTokenPayload>("/auth/refresh", payload);
}

export function logout(payload: RefreshTokenPayload): Promise<void> {
  return apiPost<void, RefreshTokenPayload>("/auth/logout", payload);
}
