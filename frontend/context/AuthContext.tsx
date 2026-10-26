"use client";

import { useRouter } from "next/navigation";
import {
  createContext,
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";
import { api } from "@/lib/api";
import { API_BASE, REFRESH_STORAGE_KEY, TOKEN_STORAGE_KEY } from "@/lib/constants";
import {
  clearAuth,
  getStoredRefreshToken,
  getStoredToken,
  getStoredUser,
  isTokenExpired,
  storeAuth,
} from "@/lib/auth";
import type { AuthTokens, User } from "@/types";

// ---------------------------------------------------------------------------
// Backend response shapes (snake_case from FastAPI)
// ---------------------------------------------------------------------------

/** Returned by POST /auth/oauth/exchange and POST /auth/refresh */
interface BackendToken {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

/** Returned by GET /auth/me */
interface BackendUser {
  user_id: number;
  email: string;
  full_name: string;
  tier: string;
  created_at: string;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Map the backend Token schema to the frontend AuthTokens shape. */
function mapTokens(raw: BackendToken): AuthTokens {
  return {
    accessToken: raw.access_token,
    refreshToken: raw.refresh_token,
    // Backend doesn't return expiresIn; decode from the JWT payload instead.
    expiresIn: 0,
  };
}

/** Map the backend UserResponse schema to the frontend User shape. */
function mapUser(raw: BackendUser): User {
  return {
    id: String(raw.user_id),
    name: raw.full_name,
    email: raw.email,
    tier: raw.tier,
    createdAt: raw.created_at,
  };
}

async function swapCodeForTokens(code: string): Promise<BackendToken | null> {
  // Raw fetch on purpose: a 401 here means the one-time code expired, which is
  // not a session problem, so it must not trigger the refresh interceptor.
  const response = await fetch(`${API_BASE}/auth/oauth/exchange`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ code }),
  });

  if (!response.ok) return null;
  return (await response.json()) as BackendToken;
}

async function revokeSession(refreshToken: string): Promise<void> {
  try {
    await fetch(`${API_BASE}/auth/logout`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
      keepalive: true,
    });
  } catch {
    // The local session is cleared either way; the token expires on its own.
  }
}

// ---------------------------------------------------------------------------
// Context
// ---------------------------------------------------------------------------

interface AuthContextValue {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  /** Trade the one-time code from the OAuth redirect for a token pair. */
  completeSignIn: (code: string) => Promise<boolean>;
  logout: () => void;
  refreshToken: () => Promise<boolean>;
}

export const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const token = getStoredToken();
    const storedUser = getStoredUser();
    if (token && storedUser && !isTokenExpired(token)) {
      setUser(storedUser);
    } else if (token) {
      clearAuth();
    }
    setIsLoading(false);
  }, []);

  // A request that could not be refreshed announces it once. The provider
  // clears the session and navigates without a full document reload.
  useEffect(() => {
    const onUnauthorized = () => {
      clearAuth();
      setUser(null);
      router.replace("/login");
    };
    window.addEventListener("omniapi:unauthorized", onUnauthorized);
    return () =>
      window.removeEventListener("omniapi:unauthorized", onUnauthorized);
  }, [router]);

  const completeSignIn = useCallback(async (code: string): Promise<boolean> => {
    const tokenRes = await swapCodeForTokens(code);
    if (!tokenRes) return false;

    const tokens = mapTokens(tokenRes);

    // Store the pair before asking who the token belongs to.
    localStorage.setItem(TOKEN_STORAGE_KEY, tokens.accessToken);
    localStorage.setItem(REFRESH_STORAGE_KEY, tokens.refreshToken);

    try {
      const userRes = await api.get<BackendUser>("/auth/me");
      const mappedUser = mapUser(userRes);
      storeAuth(tokens, mappedUser);
      setUser(mappedUser);
      return true;
    } catch {
      clearAuth();
      return false;
    }
  }, []);

  const logout = useCallback(() => {
    const refreshToken = getStoredRefreshToken();
    if (refreshToken) {
      void revokeSession(refreshToken);
    }
    clearAuth();
    setUser(null);
    router.push("/login");
  }, [router]);

  const refreshToken = useCallback(async (): Promise<boolean> => {
    try {
      const current = getStoredRefreshToken();
      if (!current) {
        clearAuth();
        setUser(null);
        return false;
      }

      // Rotation is enforced: the old refresh token is revoked, so both
      // tokens in the response replace whatever is stored.
      const response = await fetch(`${API_BASE}/auth/refresh`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: current }),
      });
      if (!response.ok) {
        clearAuth();
        setUser(null);
        return false;
      }

      const tokens = mapTokens((await response.json()) as BackendToken);
      localStorage.setItem(TOKEN_STORAGE_KEY, tokens.accessToken);
      localStorage.setItem(REFRESH_STORAGE_KEY, tokens.refreshToken);

      const userRes = await api.get<BackendUser>("/auth/me");
      const mappedUser = mapUser(userRes);
      storeAuth(tokens, mappedUser);
      setUser(mappedUser);
      return true;
    } catch {
      clearAuth();
      setUser(null);
      return false;
    }
  }, []);

  const value = useMemo(
    () => ({
      user,
      isAuthenticated: !!user,
      isLoading,
      completeSignIn,
      logout,
      refreshToken,
    }),
    [user, isLoading, completeSignIn, logout, refreshToken]
  );

  return (
    <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
  );
}
