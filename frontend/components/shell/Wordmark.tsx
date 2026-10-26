import Link from "next/link";
import { cn } from "@/lib/utils";

/**
 * The mark is the concept: a spine with three branches leaving it.
 * Ink strokes, one accent dot at the origin.
 */
export function Wordmark({ className }: { className?: string }) {
  return (
    <span className={cn("wordmark inline-flex items-center gap-2.5", className)}>
      <svg
        width="18"
        height="18"
        viewBox="0 0 18 18"
        fill="none"
        aria-hidden
        className="shrink-0"
      >
        <path
          d="M3 1.5v15"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinecap="round"
        />
        <path
          d="M3 4.5h4.5M3 9h6.5M3 13.5h4.5"
          stroke="currentColor"
          strokeWidth="1.25"
          strokeLinecap="round"
          opacity="0.55"
        />
        <circle cx="3" cy="9" r="2.1" fill="var(--c-accent)" className="wordmark__dot" />
      </svg>
      <span className="text-[1.0625rem] font-bold leading-none tracking-[-0.025em] [font-variation-settings:'wdth'_110]">
        OmniAPI
      </span>
    </span>
  );
}

export function WordmarkLink({
  className,
  onClick,
}: {
  className?: string;
  onClick?: () => void;
}) {
  return (
    <Link
      href="/dashboard"
      onClick={onClick}
      className={cn(
        "inline-flex items-center text-ink transition-opacity hover:opacity-80",
        className
      )}
    >
      <Wordmark />
      <span className="sr-only">OmniAPI dashboard</span>
    </Link>
  );
}
