"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { useAuth } from "@/hooks/useAuth";

/**
 * The page is always rendered, so its heading, landmarks and copy are in the
 * first byte of HTML. A missing session covers the page instead of replacing
 * it: the document stays real for crawlers and the measured first paint.
 */
export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.replace("/login");
    }
  }, [isAuthenticated, isLoading, router]);

  if (!isLoading && !isAuthenticated) {
    return (
      <div className="fixed inset-0 z-50 grid place-items-center bg-ground">
        <p className="label-wire" role="status">
          Redirecting to sign in
        </p>
      </div>
    );
  }

  return <>{children}</>;
}
