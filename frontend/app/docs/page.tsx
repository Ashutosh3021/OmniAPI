"use client";

import { useState } from "react";
import { DOCS_SECTIONS } from "@/lib/constants";
import { DOCS_CONTENT } from "@/lib/content/docs";
import { cn } from "@/lib/utils";

export default function DocsPage() {
  const [active, setActive] = useState<string>(DOCS_SECTIONS[0].id);
  const Section = DOCS_CONTENT[active] ?? DOCS_CONTENT["getting-started"];

  return (
    <div className="mx-auto w-full max-w-shell px-4 py-10 md:px-8 lg:py-16">
      <header className="mb-8 border-b border-ink/12 pb-8">
        <h1 className="t-title text-ink">Documentation</h1>
        <p className="mt-2 max-w-prose text-ui text-muted">
          Guides, examples and the full endpoint list for the OmniAPI gateway.
        </p>
      </header>

      <div className="grid grid-cols-1 gap-10 lg:grid-cols-12 lg:gap-gutter">
        {/* The rail is a spine: one tick per section. */}
        <aside className="lg:col-span-2">
          <div className="sticky top-24">
            <p className="label-wire mb-3 hidden lg:block">Sections</p>
            <div className="relative">
              <span data-pulse-rail className="rail-glow" aria-hidden />
              <svg
                className="pointer-events-none absolute left-0 top-0 hidden h-full w-px lg:block"
                preserveAspectRatio="none"
                aria-hidden
              >
                <line
                  x1="0.5"
                  y1="0"
                  x2="0.5"
                  y2="100"
                  className="fan-spine-base"
                  vectorEffect="non-scaling-stroke"
                />
                <line
                  data-pulse
                  x1="0.5"
                  y1="0"
                  x2="0.5"
                  y2="100"
                  className="fan-pulse"
                  vectorEffect="non-scaling-stroke"
                />
              </svg>

              <ul className="flex gap-1 overflow-x-auto pb-2 lg:flex-col lg:gap-0.5 lg:overflow-visible lg:pb-0">
                {DOCS_SECTIONS.map((section) => {
                  const isActive = active === section.id;
                  return (
                    <li key={section.id} className="shrink-0 lg:shrink">
                      <button
                        type="button"
                        onClick={() => setActive(section.id)}
                        aria-current={isActive ? "true" : undefined}
                        className={cn(
                          "tick h-9 whitespace-nowrap text-ui lg:h-10",
                          isActive
                            ? "font-medium text-ink"
                            : "text-muted hover:text-ink"
                        )}
                      >
                        <span className="tick__label">{section.title}</span>
                      </button>
                    </li>
                  );
                })}
              </ul>
            </div>
          </div>
        </aside>

        <article className="min-w-0 lg:col-span-10 lg:col-start-3">
          <h2 className="t-heading mb-6 text-ink">
            {DOCS_SECTIONS.find((s) => s.id === active)?.title}
          </h2>
          <Section />
        </article>
      </div>
    </div>
  );
}
