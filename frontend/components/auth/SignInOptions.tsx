"use client";

import { useEffect, useState } from "react";
import {
  fetchOAuthProviders,
  signInErrorMessage,
  startOAuth,
  type OAuthProvider,
} from "@/lib/oauth";

const BRAND_MARKS: Record<string, React.ReactNode> = {
  google: (
    <svg viewBox="0 0 24 24" className="h-[18px] w-[18px]" aria-hidden>
      <path
        fill="currentColor"
        d="M21.35 11.1h-9.17v2.73h6.51c-.33 3.81-3.5 5.44-6.5 5.44C8.36 19.27 5 16.25 5 12c0-4.1 3.2-7.27 7.2-7.27 3.09 0 4.9 1.97 4.9 1.97L19 4.72S16.56 2 12.1 2C6.42 2 2.03 6.8 2.03 12c0 5.05 4.13 10 10.22 10 5.35 0 9.25-3.67 9.25-9.09 0-1.15-.15-1.81-.15-1.81z"
      />
    </svg>
  ),
  github: (
    <svg viewBox="0 0 24 24" className="h-[18px] w-[18px]" aria-hidden>
      <path
        fill="currentColor"
        d="M12 .5C5.73.5.5 5.73.5 12c0 5.08 3.29 9.39 7.86 10.91.58.11.79-.25.79-.56 0-.27-.01-1.17-.02-2.12-3.2.7-3.88-1.36-3.88-1.36-.52-1.33-1.28-1.68-1.28-1.68-1.05-.72.08-.7.08-.7 1.16.08 1.77 1.19 1.77 1.19 1.03 1.77 2.7 1.26 3.36.96.1-.75.4-1.26.73-1.55-2.56-.29-5.25-1.28-5.25-5.7 0-1.26.45-2.29 1.19-3.1-.12-.29-.52-1.46.11-3.05 0 0 .97-.31 3.18 1.18a11.1 11.1 0 0 1 2.9-.39c.98 0 1.97.13 2.9.39 2.2-1.49 3.17-1.18 3.17-1.18.63 1.59.23 2.76.11 3.05.74.81 1.19 1.84 1.19 3.1 0 4.43-2.69 5.41-5.26 5.69.41.35.78 1.05.78 2.12 0 1.53-.01 2.77-.01 3.15 0 .31.21.67.8.56A11.5 11.5 0 0 0 23.5 12C23.5 5.73 18.27.5 12 .5z"
      />
    </svg>
  ),
};

export function SignInOptions() {
  const [providers, setProviders] = useState<OAuthProvider[] | null>(null);
  const [failed, setFailed] = useState(false);
  const [reason, setReason] = useState<string | null>(null);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    setReason(signInErrorMessage(params.get("error")));

    // The reason has been read; clear it so a reload does not repeat it.
    if (params.has("error")) {
      window.history.replaceState({}, "", window.location.pathname);
    }

    let cancelled = false;
    fetchOAuthProviders()
      .then((list) => {
        if (!cancelled) setProviders(list);
      })
      .catch(() => {
        if (!cancelled) setFailed(true);
      });

    return () => {
      cancelled = true;
    };
  }, []);

  if (failed) {
    return (
      <p className="border-l-2 border-bad pl-3 text-ui text-muted" role="alert">
        The gateway did not answer when asked which providers it supports.
        Reload the page to try again.
      </p>
    );
  }

  if (providers === null) {
    return (
      <p className="text-ui text-muted" role="status">
        Checking which providers this deployment supports.
      </p>
    );
  }

  if (providers.length === 0) {
    return (
      <div className="flex flex-col gap-3">
        <p className="text-ui text-ink">Sign-in is not configured yet.</p>
        <p className="text-meta text-muted">
          This deployment has no OAuth credentials. An operator has to set
          <code className="mx-1 font-mono text-[0.8125rem] text-ink">
            GOOGLE_CLIENT_ID
          </code>
          or
          <code className="mx-1 font-mono text-[0.8125rem] text-ink">
            GITHUB_CLIENT_ID
          </code>
          on the API before anyone can sign in.
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-5">
      {reason && (
        <p className="border-l-2 border-bad pl-3 text-ui text-muted" role="alert">
          {reason}
        </p>
      )}

      <div className="flex flex-col gap-2.5">
        {providers.map((provider) => (
          <button
            key={provider.id}
            type="button"
            onClick={() => startOAuth(provider.id)}
            className="btn btn-secondary flex w-full items-center justify-center gap-2.5 rounded border border-ink/25 bg-transparent px-4 py-3 text-ui font-medium text-ink transition-colors hover:border-accent/45"
          >
            <span className="btn__label inline-flex items-center gap-2.5">
              {BRAND_MARKS[provider.id]}
              Continue with {provider.name}
            </span>
            <span
              className="btn__ghost inline-flex items-center gap-2.5"
              aria-hidden
            >
              {BRAND_MARKS[provider.id]}
              Continue with {provider.name}
            </span>
          </button>
        ))}
      </div>

      <p className="text-meta text-muted">
        No password, and nothing to remember. Your account is created the first
        time a provider signs you in.
      </p>
    </div>
  );
}
