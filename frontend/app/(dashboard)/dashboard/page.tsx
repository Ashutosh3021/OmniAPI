"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import dynamic from "next/dynamic";
import { ArrowRight } from "lucide-react";
import { FanDiagram } from "@/components/fan/FanDiagram";
import { MetricStrip } from "@/components/dashboard/MetricStrip";
import { ServiceTable } from "@/components/dashboard/ServiceTable";
import { EmptyState } from "@/components/shared/EmptyState";
import { PageHeader } from "@/components/shared/PageHeader";
import { Spinner } from "@/components/shared/Spinner";
import { api } from "@/lib/api";
import type { AnalyticsSummary } from "@/types";
import type { AnalyticsResponse } from "@/types/analytics";

const formatCalls = (n: number) =>
  n >= 1_000_000
    ? `${(n / 1_000_000).toFixed(1)}M`
    : n >= 1_000
      ? `${(n / 1_000).toFixed(1)}k`
      : n.toLocaleString();

// The chart library is only needed once there is something to draw, so it
// stays out of the first load.
const CachePieChart = dynamic(
  () => import("@/components/charts/PieChart").then((m) => m.CachePieChart),
  {
    ssr: false,
    loading: () => <div className="h-[220px] w-full" aria-hidden />,
  }
);

export default function DashboardPage() {
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
  const [usage, setUsage] = useState<AnalyticsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const [summaryRes, usageRes] = await Promise.all([
          api.get<AnalyticsSummary>("/analytics/summary"),
          api.get<AnalyticsResponse>("/analytics/usage", { period: "last_24h" }),
        ]);
        if (cancelled) return;
        setSummary(summaryRes);
        setUsage(usageRes);
      } catch {
        if (!cancelled) setFailed(true);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, []);

  if (loading) return <Spinner full label="Loading the overview" />;

  if (failed) {
    return (
      <>
        <PageHeader section="overview" title="Overview" />
        <EmptyState
          title="The analytics API did not answer."
          description="The gateway may be waking up, or the request timed out. Reload to try again."
        />
      </>
    );
  }

  const rows = usage?.by_service ?? [];
  const totalCalls = rows.reduce((sum, r) => sum + r.call_count, 0);
  const cacheHits = rows.reduce((sum, r) => sum + r.cache_hits, 0);
  const cacheRate = totalCalls ? Math.round((cacheHits / totalCalls) * 100) : 0;

  return (
    <>
      <PageHeader
        section="overview"
        title="Overview"
        description="Where your calls went in the last 24 hours, and what came back."
        action={
          <Link
            href="/analytics"
            className="group inline-flex items-center gap-2 text-ui font-medium text-accent"
          >
            <span className="link">All analytics</span>
            <ArrowRight
              className="h-4 w-4 transition-transform duration-200 group-hover:translate-x-1"
              aria-hidden
            />
          </Link>
        }
      />

      {/* The fan: one request, one branch per service, one envelope. */}
      <section className="panel mb-8 p-5 md:p-7" aria-label="Call fan">
        <div className="mb-5 flex flex-wrap items-baseline justify-between gap-2">
          <h2 className="t-subhead text-ink">Where the calls went</h2>
          <p className="label-wire">
            {rows.length} {rows.length === 1 ? "service" : "services"} · last 24
            hours
          </p>
        </div>

        {rows.length > 0 ? (
          <FanDiagram
            services={rows.map((r) => ({
              name: r.service_name,
              latencyMs: Math.round(r.avg_response_time_ms),
              meta: `${r.call_count.toLocaleString()} calls`,
            }))}
            mode="loop"
            caption="Line length is the average response time of each service. The figures come from your own traffic."
          />
        ) : (
          <EmptyState
            title="Nothing is patched here yet."
            description="Connect a provider under External services, then make a call. It will show up here."
            action={
              <Link
                href="/external-services"
                className="link text-ui font-medium text-accent"
              >
                Connect a service
              </Link>
            }
          />
        )}
      </section>

      <MetricStrip
        className="mb-10"
        metrics={[
          {
            label: "Calls in 24 hours",
            value: formatCalls(summary?.calls_today ?? 0),
            note:
              summary && summary.calls_change !== 0
                ? `${summary.calls_change > 0 ? "+" : ""}${summary.calls_change}% against the previous 24 hours`
                : "No change against the previous 24 hours",
          },
          {
            label: "Served from cache",
            value: `${summary?.cache_hit_percent ?? 0}%`,
            note: `${cacheHits.toLocaleString()} of ${totalCalls.toLocaleString()} calls`,
          },
          {
            label: "Average response",
            value: `${Math.round(summary?.avg_response_ms ?? 0)} ms`,
            note:
              summary && summary.response_change_ms !== 0
                ? `${summary.response_change_ms > 0 ? "+" : ""}${summary.response_change_ms} ms against the previous 24 hours`
                : "Unchanged over the previous 24 hours",
            tone:
              summary && summary.response_change_ms > 0 ? "bad" : "neutral",
          },
        ]}
      />

      <div className="grid grid-cols-1 gap-gutter lg:grid-cols-12">
        <section className="panel p-5 md:p-7 lg:col-span-7" aria-label="Services">
          <h2 className="t-subhead mb-4 text-ink">Per service</h2>
          <ServiceTable rows={rows} />
        </section>

        <section
          className="panel flex flex-col p-5 md:p-7 lg:col-span-5"
          aria-label="Cache share"
        >
          <h2 className="t-subhead mb-2 text-ink">Cache share</h2>
          <p className="text-meta text-muted">
            Calls answered from Redis never touched the provider.
          </p>
          <div className="mt-4 flex-1">
            <CachePieChart
              data={[
                { name: "Cache hit", value: cacheHits },
                { name: "Cache miss", value: Math.max(totalCalls - cacheHits, 0) },
              ]}
            />
          </div>
          <p className="mt-2 text-center text-[2rem] font-bold leading-none tracking-[-0.03em] num text-ink [font-variation-settings:'wdth'_108]">
            {cacheRate}%
          </p>
        </section>
      </div>
    </>
  );
}
