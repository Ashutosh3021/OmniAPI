"use client";

import { Moon, Sun } from "lucide-react";
import { PageHeader } from "@/components/shared/PageHeader";
import { Badge } from "@/components/shared/Badge";
import { useAuth } from "@/hooks/useAuth";
import { useTheme } from "@/context/ThemeContext";
import { formatDate } from "@/lib/utils";

const SECTIONS = [
  { id: "account", title: "Account" },
  { id: "appearance", title: "Appearance" },
  { id: "plan", title: "Plan" },
];

export default function SettingsPage() {
  const { user } = useAuth();
  const { theme, setTheme } = useTheme();

  return (
    <>
      <PageHeader
        meta="this device"
        title="Settings"
        description="Your account, how the dashboard looks, and what the gateway allows your tier to do."
      />

      <div className="grid grid-cols-1 gap-10 lg:grid-cols-12 lg:gap-gutter">
        <aside className="lg:col-span-3">
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
            </svg>
            <ul className="flex flex-col gap-0.5">
              {SECTIONS.map((s) => (
                <li key={s.id}>
                  <a
                    href={`#${s.id}`}
                    className="tick h-10 text-ui text-muted transition-colors hover:text-ink"
                  >
                    <span className="tick__label">{s.title}</span>
                  </a>
                </li>
              ))}
            </ul>
          </div>
        </aside>

        <div className="flex flex-col gap-6 lg:col-span-9">
          <section id="account" className="panel p-5 md:p-7">
            <h2 className="t-subhead mb-4 text-ink">Account</h2>
            <dl className="space-y-2.5 text-ui">
              <div className="flex justify-between gap-4">
                <dt className="text-muted">Name</dt>
                <dd className="text-ink">{user?.name || "Not set"}</dd>
              </div>
              <div className="flex justify-between gap-4">
                <dt className="text-muted">Email</dt>
                <dd className="text-ink">{user?.email || "Not set"}</dd>
              </div>
              {user?.createdAt && (
                <div className="flex justify-between gap-4">
                  <dt className="text-muted">Member since</dt>
                  <dd className="text-ink">{formatDate(user.createdAt)}</dd>
                </div>
              )}
            </dl>
            <p className="mt-5 border-t border-ink/12 pt-4 text-meta text-muted">
              The gateway does not expose an endpoint to change these details
              yet, so they are shown exactly as the account holds them.
            </p>
          </section>

          <section id="appearance" className="panel p-5 md:p-7">
            <h2 className="t-subhead mb-1 text-ink">Appearance</h2>
            <p className="mb-5 text-meta text-muted">
              Both themes are drawn for this dashboard. The choice is stored on
              this device.
            </p>
            <div
              className="inline-flex rounded border border-ink/15 p-0.5"
              role="group"
              aria-label="Colour theme"
            >
              {(
                [
                  { value: "light", label: "Light", Icon: Sun },
                  { value: "dark", label: "Dark", Icon: Moon },
                ] as const
              ).map(({ value, label, Icon }) => (
                <button
                  key={value}
                  type="button"
                  onClick={() => setTheme(value)}
                  aria-pressed={theme === value}
                  className={
                    theme === value
                      ? "flex items-center gap-2 rounded-[3px] bg-ink px-3 py-1.5 text-ui text-ground transition-colors"
                      : "flex items-center gap-2 rounded-[3px] px-3 py-1.5 text-ui text-muted transition-colors hover:text-ink"
                  }
                >
                  <Icon className="h-3.5 w-3.5" aria-hidden />
                  {label}
                </button>
              ))}
            </div>
          </section>

          <section id="plan" className="panel p-5 md:p-7">
            <h2 className="t-subhead mb-4 text-ink">Plan</h2>
            <div className="flex flex-wrap items-center gap-3">
              <Badge tone="accent">{user?.tier || "free"}</Badge>
              <p className="text-ui text-muted">
                The gateway enforces a per-tier call limit on every orchestrate
                response and returns it in the X-RateLimit headers.
              </p>
            </div>
            <p className="mt-5 border-t border-ink/12 pt-4 text-meta text-muted">
              No payment provider is connected to this deployment, so there is
              no invoice, no card and no upgrade button to show here.
            </p>
          </section>
        </div>
      </div>
    </>
  );
}
