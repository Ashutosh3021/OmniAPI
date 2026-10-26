"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { AuthCard } from "@/components/auth/AuthCard";
import { ButtonLink } from "@/components/shared/Button";
import { Spinner } from "@/components/shared/Spinner";
import { useAuth } from "@/hooks/useAuth";

export function AuthCallback() {
  const { completeSignIn } = useAuth();
  const router = useRouter();
  const [failed, setFailed] = useState(false);
  const started = useRef(false);

  useEffect(() => {
    if (started.current) return;
    started.current = true;

    const params = new URLSearchParams(window.location.search);
    const error = params.get("error");
    if (error) {
      router.replace(`/login?error=${encodeURIComponent(error)}`);
      return;
    }

    const code = params.get("code");
    if (!code) {
      router.replace("/login?error=missing_code");
      return;
    }

    // The code is single-use. Clear it before the exchange so a reload can
    // never replay it, then trade it for the token pair.
    window.history.replaceState({}, "", "/auth/callback");

    completeSignIn(code).then((ok) => {
      if (ok) {
        router.replace("/dashboard");
      } else {
        setFailed(true);
      }
    });
  }, [completeSignIn, router]);

  if (failed) {
    return (
      <AuthCard
        title="Sign-in did not complete"
        subtitle="The one-time code was expired or already used."
      >
        <div className="flex flex-col gap-5">
          <p className="border-l-2 border-bad pl-3 text-ui text-muted" role="alert">
            Nothing was stored. Start again from the sign-in page.
          </p>
          <ButtonLink href="/login" fullWidth>
            Back to sign in
          </ButtonLink>
        </div>
      </AuthCard>
    );
  }

  return (
    <AuthCard
      title="Signing you in"
      subtitle="One moment while the gateway exchanges the code."
    >
      <Spinner label="Exchanging the one-time code" />
    </AuthCard>
  );
}
