export interface User {
  id: string;
  name: string;
  email: string;
  company?: string;
  /** Plan tier reported by the gateway. */
  tier?: string;
  /** ISO timestamp of when the account was created. */
  createdAt?: string;
}

export interface AuthTokens {
  accessToken: string;
  refreshToken: string;
  expiresIn: number;
}

export interface LoginResponse {
  user: User;
  tokens: AuthTokens;
}

export interface SignupResponse {
  user: User;
  tokens: AuthTokens;
}
