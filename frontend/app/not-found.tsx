import type { Metadata } from "next";
import Link from "next/link";
import { ButtonLink } from "@/components/shared/Button";
import { Wordmark } from "@/components/shell/Wordmark";

export const metadata: Metadata = {
  title: "No route to this page",
  description: "The page you asked for is not on this gateway.",
  robots: { index: false, follow: true },
};

/** The concept's dead end: one branch leaves the spine and goes nowhere. */
function DeadEnd() {
  return (
    <svg
      viewBox="0 0 420 160"
      className="w-full max-w-[420px]"
      role="img"
      aria-label="A request line leaving the spine and ending without an answer"
    >
      <line
        x1="28"
        y1="20"
        x2="28"
        y2="140"
        className="fan-spine fan-spine-base"
      />
      <line
        data-pulse
        x1="28"
        y1="20"
        x2="28"
        y2="140"
        className="fan-pulse"
      />
      <circle cx="28" cy="80" r="4" className="fan-packet" />

      <path
        d="M28,50 C70,50 90,50 120,50 L200,50"
        className="fan-flow"
        fill="none"
      />
      <path
        d="M28,50 C70,50 90,50 120,50 L200,50"
        className="fan-branch"
        fill="none"
      />
      <circle cx="200" cy="50" r="3" className="fan-packet" />

      <path
        d="M28,110 C70,110 96,110 130,110 L170,110"
        className="fan-branch fan-branch--idle"
        fill="none"
        strokeDasharray="4 6"
      />
      <g stroke="var(--c-bad)" strokeWidth="1.75" strokeLinecap="round">
        <line x1="182" y1="102" x2="196" y2="116" />
        <line x1="196" y1="102" x2="182" y2="116" />
      </g>
    </svg>
  );
}

export default function NotFound() {
  return (
    <div className="flex min-h-dvh flex-col bg-ground">
      <header className="border-b border-ink/12 px-4 py-5 md:px-8">
        <Link
          href="/"
          className="inline-flex text-ink transition-opacity hover:opacity-70"
          aria-label="OmniAPI home"
        >
          <Wordmark />
        </Link>
      </header>

      <main
        id="main"
        tabIndex={-1}
        className="mx-auto flex w-full max-w-shell flex-1 flex-col justify-center px-4 py-16 md:px-8"
      >
        <p className="label-wire">404 · no route</p>
        <h1 className="t-title mt-4 max-w-[20ch] text-ink">
          This branch does not lead anywhere.
        </h1>
        <p className="mt-4 max-w-prose text-ui text-muted">
          The gateway has no route for that address. It might have been moved,
          or the link might have been mistyped.
        </p>

        <div className="my-10">
          <DeadEnd />
        </div>

        <div className="flex flex-wrap gap-3">
          <ButtonLink href="/">Back to the start</ButtonLink>
          <ButtonLink href="/docs" variant="secondary">
            Read the docs
          </ButtonLink>
        </div>
      </main>
    </div>
  );
}
