"use client";

import { useEffect, useState } from "react";
import { PageHeader } from "@/components/shared/PageHeader";
import { Spinner } from "@/components/shared/Spinner";
import { EmptyState } from "@/components/shared/EmptyState";
import { MetricStrip } from "@/components/dashboard/MetricStrip";
import { ServiceTable } from "@/components/dashboard/ServiceTable";
import { BarList } from "@/components/charts/BarList";
import { CacheRing } from "@/components/charts/Ring";
import { ExportReport } from "@/components/analytics/ExportReport";
import { api } from "@/lib/api";
import type { AnalyticsResponse } from "@/types/analytics";

const PERIODS = [
  { value: "last_24h", label: "24 hours" },
  { value: "last_7d", label: "7 days" },
  { value: "last_30d", label: "30 days" },
] as const;

type Period = (typeof PERIODS)[number]["value"];

export default function AnalyticsPage() {
  const [period, setPeriod] = useState<Period>("last_24h");
  const [data, setData] = useState<AnalyticsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setFailed(false);

    api
      .get<AnalyticsResponse>("/analytics/usage", { period })
      .then((res) => {
        if (!cancelled) setData(res);
      })
      .catch(() => {
        if (!cancelled) setFailed(true);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [period]);

  const rows = data?.by_service ?? [];
  const metrics = data?.metrics;

  const exportRows = rows.map((r) => ({
    service: r.service_name,
    calls: r.call_count,
    cacheHits: r.cache_hits,
    avgResponseMs: Math.round(r.avg_response_time_ms),
    errors: r.error_count,
  }));

  return (
    <>
      <PageHeader
        meta="from the usage log"
        title="Analytics"
        description="Every number here comes from your own usage log."
        action={
          <div className="flex flex-wrap items-center gap-2">
            <div
              className="flex rounded border border-ink/15 p-0.5"
              role="group"
              aria-label="Time period"
            >
              {PERIODS.map((p) => (
                <button
                  key={p.value}
                  type="button"
                  onClick={() => setPeriod(p.value)}
                  aria-pressed={period === p.value}
                  className={
                    period === p.value
                      ? "rounded-[3px] bg-ink px-2.5 py-1 font-mono text-micro uppercase tracking-[0.06em] text-ground transition-colors"
                      : "rounded-[3px] px-2.5 py-1 font-mono text-micro uppercase tracking-[0.06em] text-muted transition-colors hover:text-ink"
                  }
                >
                  {p.label}
                </button>
              ))}
            </div>
            <ExportReport data={exportRows} />
          </div>
        }
      />

      {failed ? (
        <EmptyState
          title="The analytics API did not answer."
          description="Reload to try again. If it keeps failing, check that the gateway is running."
        />
      ) : loading || !metrics ? (
        <Spinner label="Loading analytics" />
      ) : (
        <>
          <MetricStrip
            className="mb-10"
            metrics={[
              {
                label: "Total calls",
                value: metrics.total_calls.toLocaleString(),
                note: `${metrics.successful_calls.toLocaleString()} succeeded, ${metrics.failed_calls.toLocaleString()} failed`,
              },
              {
                label: "Served from cache",
                value: `${Math.round(metrics.cache_hit_rate * 100)}%`,
                note: `${metrics.cache_hits.toLocaleString()} calls never reached the provider`,
              },
              {
                label: "Average response",
                value: `${Math.round(metrics.avg_response_time_ms)} ms`,
                note: "Across every service in this period",
              },
              {
                label: "Provider time saved",
                value: `$${metrics.estimated_cost_saved.toFixed(4)}`,
                note: "Estimated from the calls the cache absorbed",
              },
            ]}
          />

          <div className="grid grid-cols-1 gap-gutter lg:grid-cols-12">
            <section className="panel p-5 md:p-7 lg:col-span-7">
              <h2 className="t-subhead mb-1 text-ink">Calls per service</h2>
              <p className="mb-8 text-meta text-muted">
                Which providers took the traffic.
              </p>
              <BarList
                rows={rows.map((r) => ({
                  label: r.service_name,
                  value: r.call_count,
                }))}
              />
            </section>

            <section className="panel flex flex-col p-5 md:p-7 lg:col-span-5">
              <h2 className="t-subhead mb-1 text-ink">Cache share</h2>
              <p className="mb-4 text-meta text-muted">
                How much of the traffic Redis absorbed.
              </p>
              <div className="flex flex-1 items-center justify-center">
                <CacheRing
                  value={metrics.cache_hits}
                  total={metrics.total_calls}
                  caption="from cache"
                />
              </div>
            </section>
          </div>

          <section className="panel mt-6 p-5 md:p-7">
            <h2 className="t-subhead mb-4 text-ink">Per service breakdown</h2>
            <ServiceTable rows={rows} />
          </section>
        </>
      )}
    </>
  );
}
