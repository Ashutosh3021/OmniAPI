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
import {
  clearAuth,
  getStoredToken,
  getStoredUser,
  isTokenExpired,
  storeAuth,
} from "@/lib/auth";
import type { AuthTokens, User } from "@/types";
import type { LoginInput, SignupInput } from "@/lib/validators";

// ---------------------------------------------------------------------------
// Backend response shapes (snake_case from FastAPI)
// ---------------------------------------------------------------------------

/** Returned by POST /auth/login and POST /auth/refresh */
interface BackendToken {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

/** Returned by GET /auth/me and POST /auth/register */
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
  };
}

// ---------------------------------------------------------------------------
// Context
// ---------------------------------------------------------------------------

interface AuthContextValue {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (data: LoginInput) => Promise<boolean>;
  signup: (data: SignupInput) => Promise<boolean>;
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

  const login = useCallback(
    async (data: LoginInput): Promise<boolean> => {
      try {
        // 1. Obtain token pair — backend returns { access_token, refresh_token }
        const tokenRes = await api.post<BackendToken>("/auth/login", data);
        const tokens = mapTokens(tokenRes);

        // 2. Temporarily store the access token so the next request is authenticated
        localStorage.setItem("omniapi_access_token", tokens.accessToken);

        // 3. Fetch the user profile
        const userRes = await api.get<BackendUser>("/auth/me");
        const mappedUser = mapUser(userRes);

        // 4. Persist both and update state
        storeAuth(tokens, mappedUser);
        setUser(mappedUser);
        router.push("/dashboard");
        return true;
      } catch {
        return false;
      }
    },
    [router]
  );

  const signup = useCallback(
    async (data: SignupInput): Promise<boolean> => {
      try {
        // Backend route is POST /auth/register (not /auth/signup).
        // It returns a UserResponse (no tokens), so we register then log in.
        await api.post<BackendUser>("/auth/register", {
          full_name: data.name,
          email: data.email,
          password: data.password,
        });
        return await login({ email: data.email, password: data.password });
      } catch {
        return false;
      }
    },
    [login]
  );

  const logout = useCallback(() => {
    clearAuth();
    setUser(null);
    router.push("/login");
  }, [router]);

  const refreshToken = useCallback(async (): Promise<boolean> => {
    try {
      const tokenRes = await api.post<BackendToken>("/auth/refresh", {});
      const tokens = mapTokens(tokenRes);

      // Re-fetch user profile with the new token
      localStorage.setItem("omniapi_access_token", tokens.accessToken);
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
      login,
      signup,
      logout,
      refreshToken,
    }),
    [user, isLoading, login, signup, logout, refreshToken]
  );

  return (
    <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
  );
}
