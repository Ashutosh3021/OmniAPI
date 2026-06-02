import { API_BASE } from "./constants";
import { clearAuth, getStoredToken, getStoredRefreshToken, storeAuth } from "./auth";

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public data?: unknown
  ) {
    super(message);
    this.name = "ApiError";
  }
}

interface RequestOptions extends RequestInit {
  params?: Record<string, string>;
  skipAuthRefresh?: boolean;
}

let isRefreshing = false;
let refreshPromise: Promise<boolean> | null = null;

async function refreshAccessToken(): Promise<boolean> {
  // Prevent multiple simultaneous refresh attempts
  if (isRefreshing && refreshPromise) {
    return refreshPromise;
  }

  isRefreshing = true;
  refreshPromise = (async () => {
    try {
      const refreshToken = getStoredRefreshToken();
      if (!refreshToken) {
        return false;
      }

      const response = await fetch(`${API_BASE}/auth/refresh`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${refreshToken}`,
        },
      });

      if (!response.ok) {
        return false;
      }

      const data = await response.json();
      if (data.tokens && data.user) {
        storeAuth(data.tokens, data.user);
        return true;
      }

      return false;
    } catch {
      return false;
    } finally {
      isRefreshing = false;
      refreshPromise = null;
    }
  })();

  return refreshPromise;
}

async function request<T>(
  path: string,
  options: RequestOptions = {}
): Promise<T> {
  const { params, headers: customHeaders, skipAuthRefresh, ...init } = options;
  const token = typeof window !== "undefined" ? getStoredToken() : null;

  let url = `${API_BASE}${path}`;
  if (params) {
    const search = new URLSearchParams(params);
    url += `?${search.toString()}`;
  }

  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...customHeaders,
  };

  if (token) {
    (headers as Record<string, string>)["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(url, { ...init, headers });

  if (!response.ok) {
    // Handle 401 Unauthorized with automatic token refresh
    if (response.status === 401 && typeof window !== "undefined" && !skipAuthRefresh) {
      const refreshed = await refreshAccessToken();
      if (refreshed) {
        // Retry the original request with new token
        return request<T>(path, { ...options, skipAuthRefresh: true });
      } else {
        // Refresh failed, redirect to login
        clearAuth();
        window.location.href = "/login";
      }
    }

    let data: unknown;
    try {
      data = await response.json();
    } catch {
      data = undefined;
    }
    const message =
      typeof data === "object" &&
      data !== null &&
      "detail" in data &&
      typeof (data as { detail: string }).detail === "string"
        ? (data as { detail: string }).detail
        : typeof data === "object" &&
          data !== null &&
          "error" in data &&
          typeof (data as { error: string }).error === "string"
        ? (data as { error: string }).error
        : response.statusText;
    throw new ApiError(message, response.status, data);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

export const api = {
  get: <T>(path: string, params?: Record<string, string>) =>
    request<T>(path, { method: "GET", params }),
  post: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "POST", body: JSON.stringify(body) }),
  put: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "PUT", body: JSON.stringify(body) }),
  patch: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "PATCH", body: JSON.stringify(body) }),
  delete: <T>(path: string) => request<T>(path, { method: "DELETE" }),
};
