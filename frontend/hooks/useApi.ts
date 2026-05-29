"use client";

import { useCallback, useState } from "react";
import { ApiError, api } from "@/lib/api";

interface UseApiState {
  loading: boolean;
  error: string | null;
}

export function useApi() {
  const [state, setState] = useState<UseApiState>({
    loading: false,
    error: null,
  });

  const execute = useCallback(
    async <T>(fn: () => Promise<T>): Promise<T | null> => {
      setState({ loading: true, error: null });
      try {
        const result = await fn();
        setState({ loading: false, error: null });
        return result;
      } catch (err) {
        const message =
          err instanceof ApiError ? err.message : "Request failed";
        setState({ loading: false, error: message });
        return null;
      }
    },
    []
  );

  return { ...state, api, execute };
}
