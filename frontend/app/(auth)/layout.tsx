import Link from "next/link";
import { FanDiagram } from "@/components/fan/FanDiagram";
import { Wordmark } from "@/components/shell/Wordmark";

const promises = [
  "Provider calls run in parallel, not in a queue.",
  "Cached answers never spend your provider quota.",
  "One response shape, whatever you asked for.",
];

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-dvh lg:grid lg:grid-cols-[1.15fr_0.85fr]">
      {/* The concept, on its own field. */}
      <aside className="ink-panel hidden flex-col justify-between px-10 py-12 lg:flex xl:px-14">
        <Link href="/" className="text-ink transition-opacity hover:opacity-80">
          <Wordmark />
        </Link>

        <div className="py-10">
          <p className="t-heading max-w-[24ch] text-ink">
            Every provider you have ever added, behind a single call.
          </p>

          <div className="mt-10 max-w-[520px]">
            <FanDiagram
              services={[
                { name: "weather", latencyMs: 240 },
                { name: "news", latencyMs: 410 },
                { name: "stock", latencyMs: 180 },
              ]}
              mode="static"
            />
          </div>
        </div>

        <ul className="flex flex-col gap-2.5">
          {promises.map((p) => (
            <li
              key={p}
              className="flex items-start gap-2.5 text-ui text-muted"
            >
              <span className="lamp mt-1.5 bg-accent" aria-hidden />
              {p}
            </li>
          ))}
        </ul>
      </aside>

      <div className="flex min-h-dvh flex-col px-4 py-10 md:px-8">
        <div className="flex items-center justify-between lg:hidden">
          <Link href="/" className="text-ink" aria-label="OmniAPI home">
            <Wordmark />
          </Link>
        </div>

        <main
          id="main"
          tabIndex={-1}
          className="flex flex-1 items-center justify-center py-10"
        >
          <div className="panel w-full max-w-[440px] p-6 md:p-8">{children}</div>
        </main>
      </div>
    </div>
  );
}
