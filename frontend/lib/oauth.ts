import { API_BASE } from "./constants";

export interface OAuthProvider {
  id: string;
  name: string;
  /** False when the server has no credentials for this provider. */
  configured: boolean;
}

interface ProvidersResponse {
  providers?: OAuthProvider[];
}

/** Providers the server can actually complete a sign-in for. */
export async function fetchOAuthProviders(): Promise<OAuthProvider[]> {
  const response = await fetch(`${API_BASE}/auth/oauth/providers`, {
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error("Could not read the sign-in providers");
  }

  const data = (await response.json()) as ProvidersResponse;
  return (data.providers ?? []).filter((provider) => provider.configured);
}

/**
 * Sign-in is a full page load: the endpoint answers with a redirect to the
 * provider, which fetch() is not allowed to follow across origins.
 */
export function startOAuth(providerId: string): void {
  window.location.href = `${API_BASE}/auth/oauth/${providerId}`;
}

const SIGN_IN_ERRORS: Record<string, string> = {
  access_denied: "You cancelled at the provider. Nothing was changed.",
  missing_code: "The provider did not return a code. Try again.",
  invalid_state: "That sign-in attempt expired. Start again.",
  invalid_code: "The provider rejected the sign-in. Start again.",
  provider_unavailable: "The provider did not answer. Try again in a moment.",
  unverified_email:
    "That provider account has no verified email, so it cannot sign in.",
};

export function signInErrorMessage(code: string | null): string | null {
  if (!code) return null;
  return (
    SIGN_IN_ERRORS[code] ??
    "Sign-in did not complete. Try again, or use another provider."
  );
}
