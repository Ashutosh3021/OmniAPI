import type { Metadata } from "next";
import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { FanDiagram } from "@/components/fan/FanDiagram";
import { CodePanel } from "@/components/shared/CodePanel";
import { SiteHeader } from "@/components/shell/SiteHeader";
import { SiteFooter } from "@/components/shell/SiteFooter";
import {
  capabilities,
  demoFan,
  hero,
  pillars,
  requestExample,
  responseExample,
  steps,
} from "@/lib/content/site";

export const metadata: Metadata = {
  title: "OmniAPI — one call for every third-party API",
  description:
    "OmniAPI turns any number of third-party APIs into a single call: parallel fan-out, caching, retries and one signed response.",
  alternates: { canonical: "/" },
};

export default function HomePage() {
  return (
    <>
      <SiteHeader />

      <main id="main" tabIndex={-1}>
        {/* Poster: one statement, set wide. */}
        <section className="mx-auto w-full max-w-shell px-4 pb-14 pt-14 md:px-8 md:pt-20 lg:pb-20 lg:pt-24">
          <p className="label-wire">{hero.kicker}</p>

          <h1 className="t-display mt-6 text-ink">
            <span data-split="lines" data-intro className="block">
              One call fans out.
            </span>
            <span
              data-split="lines"
              data-intro
              className="block text-accent"
            >
              Many answers gather back.
            </span>
          </h1>

          <div className="mt-9 grid grid-cols-1 gap-8 lg:grid-cols-12">
            <p className="t-body max-w-prose text-muted lg:col-span-6">
              {hero.body}
            </p>
            <div className="flex flex-wrap items-center gap-3 lg:col-span-4 lg:col-start-9 lg:justify-end">
              <Link
                href={hero.primaryCta.href}
                className="btn btn-primary inline-flex items-center justify-center gap-2 rounded bg-accent px-5 py-3 text-ui font-medium"
              >
                <span className="btn__label inline-flex items-center gap-2">
                  {hero.primaryCta.label}
                  <ArrowRight className="h-4 w-4" aria-hidden />
                </span>
                <span
                  className="btn__ghost inline-flex items-center gap-2"
                  aria-hidden
                >
                  {hero.primaryCta.label}
                  <ArrowRight className="h-4 w-4" />
                </span>
              </Link>
              <Link
                href={hero.secondaryCta.href}
                className="btn btn-secondary inline-flex items-center justify-center rounded border border-ink/25 px-5 py-3 text-ui font-medium text-ink"
              >
                <span className="btn__label inline-flex items-center">
                  {hero.secondaryCta.label}
                </span>
                <span className="btn__ghost inline-flex items-center" aria-hidden>
                  {hero.secondaryCta.label}
                </span>
              </Link>
            </div>
          </div>
        </section>

        {/* Asymmetric pair: the diagram and the request that produces it. */}
        <section
          data-reveal="up"
          className="border-y border-ink/12 bg-surface"
        >
          <div className="mx-auto grid w-full max-w-shell grid-cols-1 gap-10 px-4 py-14 md:px-8 lg:grid-cols-12 lg:gap-gutter lg:py-20">
            <div className="lg:col-span-7">
              <p className="label-wire mb-4">the shape of a request</p>
              <div className="panel p-5 md:p-7">
                <FanDiagram
                  services={demoFan.map((s) => ({ ...s }))}
                  mode="loop"
                  caption={hero.note}
                />
              </div>
            </div>

            <div className="lg:col-span-5 lg:pt-8">
              <p className="label-wire mb-4">what you send</p>
              <CodePanel
                title="POST /orchestrate"
                language="bash"
                code={requestExample}
                className="mb-5"
              />
              <p className="label-wire mb-4">what comes back</p>
              <CodePanel
                title="response"
                language="json"
                code={responseExample}
              />
            </div>
          </div>
        </section>

        {/* Index list: the three things that happen to every request. */}
        <section className="mx-auto w-full max-w-shell px-4 py-14 md:px-8 lg:py-20">
          <h2 className="t-heading mb-8 text-ink">What happens to a request</h2>

          <ul className="border-t border-ink/12">
            {pillars.map((p) => (
              <li
                key={p.index}
                data-reveal="up"
                className="branch-row grid grid-cols-1 gap-3 border-b border-ink/12 py-7 md:grid-cols-12 md:gap-gutter"
              >
                <span className="label-wire md:col-span-1">{p.index}</span>
                <h3 className="t-subhead text-ink md:col-span-4">{p.title}</h3>
                <p className="max-w-prose text-ui text-muted md:col-span-7">
                  {p.body}
                </p>
              </li>
            ))}
          </ul>
        </section>

        {/* Gallery wall: four products, deliberately uneven. */}
        <section className="border-y border-ink/12 bg-surface">
          <div className="mx-auto w-full max-w-shell px-4 py-14 md:px-8 lg:py-20">
            <h2 className="t-heading mb-8 text-ink">
              Everything around the call
            </h2>

            <div className="grid grid-cols-1 gap-4 md:grid-cols-12 md:gap-gutter">
              {capabilities.map((c, i) => (
                <article
                  key={c.title}
                  data-reveal="up"
                  className={
                    i % 2 === 0
                      ? "panel flex flex-col p-5 md:col-span-7 md:p-7"
                      : "panel flex flex-col p-5 md:col-span-5 md:p-7"
                  }
                >
                  <p className="label-wire mb-3">{c.title}</p>
                  <p className="t-body max-w-prose text-muted">{c.body}</p>
                  <Link
                    href={c.href}
                    className="group mt-5 inline-flex w-fit items-center gap-2 text-ui font-medium text-accent"
                  >
                    <span className="link">{c.cta}</span>
                    <ArrowRight
                      className="h-4 w-4 transition-transform duration-200 group-hover:translate-x-1"
                      aria-hidden
                    />
                  </Link>
                </article>
              ))}
            </div>
          </div>
        </section>

        {/* Sequence: four steps, connected by one line. */}
        <section className="mx-auto w-full max-w-shell px-4 py-14 md:px-8 lg:py-20">
          <h2 className="t-heading mb-10 text-ink">From zero to a call</h2>

          <ol className="grid grid-cols-1 gap-8 sm:grid-cols-2 lg:grid-cols-4 lg:gap-gutter">
            {steps.map((s, i) => (
              <li key={s.title} data-reveal="up" className="relative">
                <div
                  className="mb-4 h-px w-full bg-ink/15"
                  aria-hidden
                />
                <p className="label-wire mb-2">
                  {String(i + 1).padStart(2, "0")}
                </p>
                <h3 className="t-subhead mb-2 text-ink">{s.title}</h3>
                <p className="text-ui text-muted">{s.body}</p>
              </li>
            ))}
          </ol>
        </section>

        {/* Footer as finale. */}
        <section className="border-t border-ink/12 bg-ink text-ground">
          <div className="mx-auto w-full max-w-shell px-4 py-16 md:px-8 lg:py-24">
            <p className="label-wire text-ground/60">Start here</p>
            <p className="t-title mt-4 max-w-[18ch] text-ground">
              One key is enough to make the first call.
            </p>
            <div className="mt-8 flex flex-wrap items-center gap-3">
              <Link
                href={hero.primaryCta.href}
                className="btn inline-flex items-center justify-center rounded bg-ground px-5 py-3 text-ui font-medium text-ink hover:text-ink"
              >
                <span className="btn__label inline-flex items-center gap-2">
                  {hero.primaryCta.label}
                  <ArrowRight className="h-4 w-4" aria-hidden />
                </span>
                <span
                  className="btn__ghost inline-flex items-center gap-2"
                  aria-hidden
                >
                  {hero.primaryCta.label}
                  <ArrowRight className="h-4 w-4" />
                </span>
              </Link>
              <Link
                href="/docs"
                className="btn inline-flex items-center justify-center rounded border border-ground/30 px-5 py-3 text-ui font-medium text-ground hover:border-ground/60"
              >
                <span className="btn__label inline-flex items-center">
                  {hero.secondaryCta.label}
                </span>
                <span className="btn__ghost inline-flex items-center" aria-hidden>
                  {hero.secondaryCta.label}
                </span>
              </Link>
            </div>
          </div>
        </section>
      </main>

      <SiteFooter />
    </>
  );
}
