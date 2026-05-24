export type CurrentUser = {
  user_id: string;
  empresa_id: string;
  roles: string[];
  permissions: string[];
};

export type LoginPayload = {
  email: string;
  password: string;
  empresa_id?: string;
};

export type RefreshTokenPayload = {
  refresh_token: string;
};

export type TokenResponse = {
  access_token: string;
  refresh_token: string;
  token_type: "bearer";
  expires_in: number;
};

export type AuthSession = TokenResponse & {
  user: CurrentUser;
};
