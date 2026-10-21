import Link from "next/link";
import { cn } from "@/lib/utils";
import { Wordmark } from "./Wordmark";

interface SiteHeaderProps {
  className?: string;
}

export function SiteHeader({ className }: SiteHeaderProps) {
  return (
    <header
      className={cn(
        "sticky top-0 z-40 border-b border-ink/12 bg-ground/85 backdrop-blur",
        className
      )}
    >
      <div className="mx-auto flex h-16 w-full max-w-shell items-center justify-between gap-6 px-4 md:px-8">
        <Link
          href="/"
          className="text-ink transition-opacity hover:opacity-80"
          aria-label="OmniAPI home"
        >
          <Wordmark />
        </Link>

        <nav aria-label="Primary" className="flex items-center gap-1 sm:gap-2">
          <Link
            href="/docs"
            className="rounded px-3 py-2 text-ui text-muted transition-colors hover:text-ink"
          >
            Docs
          </Link>
          <Link
            href="/login"
            className="rounded px-3 py-2 text-ui text-muted transition-colors hover:text-ink"
          >
            Sign in
          </Link>
          <Link
            href="/signup"
            className="btn btn-primary ml-1 inline-flex items-center justify-center rounded bg-accent px-3.5 py-2 text-ui font-medium sm:px-4"
          >
            <span className="btn__label inline-flex items-center">Start free</span>
            <span className="btn__ghost inline-flex items-center" aria-hidden>
              Start free
            </span>
          </Link>
        </nav>
      </div>
    </header>
  );
}
