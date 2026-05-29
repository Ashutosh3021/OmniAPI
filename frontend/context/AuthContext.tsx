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
import type { LoginResponse, SignupResponse, User } from "@/types";
import type { LoginInput, SignupInput } from "@/lib/validators";

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
        const res = await api.post<LoginResponse>("/auth/login", data);
        storeAuth(res.tokens, res.user);
        setUser(res.user);
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
        const res = await api.post<SignupResponse>("/auth/signup", {
          name: data.name,
          email: data.email,
          password: data.password,
        });
        storeAuth(res.tokens, res.user);
        setUser(res.user);
        router.push("/dashboard");
        return true;
      } catch {
        return false;
      }
    },
    [router]
  );

  const logout = useCallback(() => {
    clearAuth();
    setUser(null);
    router.push("/login");
  }, [router]);

  const refreshToken = useCallback(async (): Promise<boolean> => {
    try {
      const res = await api.post<LoginResponse>("/auth/refresh", {});
      storeAuth(res.tokens, res.user);
      setUser(res.user);
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
