"use client";

import { useEffect, useState } from "react";
import { Timer, TrendingUp, MemoryStick } from "lucide-react";
import { StatsCard } from "@/components/dashboard/StatsCard";
import { UsageChart } from "@/components/dashboard/UsageChart";
import { RecentActivity } from "@/components/dashboard/RecentActivity";
import { PageHeader } from "@/components/shared/PageHeader";
import { Spinner } from "@/components/shared/Spinner";
import { api } from "@/lib/api";
import type { ActivityLog, AnalyticsSummary, UsageDataPoint } from "@/types";

export default function DashboardPage() {
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
  const [usage, setUsage] = useState<UsageDataPoint[]>([]);
  const [activity, setActivity] = useState<ActivityLog[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [summaryRes, usageRes] = await Promise.all([
          api.get<AnalyticsSummary>("/analytics/summary"),
          api.get<{ usage: UsageDataPoint[]; activity: ActivityLog[] }>(
            "/analytics/usage"
          ),
        ]);
        setSummary(summaryRes);
        setUsage(usageRes.usage);
        setActivity(usageRes.activity);
      } catch {
        // handled by api client
      }
      setLoading(false);
    }
    load();
  }, []);

  if (loading) return <Spinner />;

  const formatCalls = (n: number) =>
    n >= 1_000_000 ? `${(n / 1_000_000).toFixed(1)}M` : n.toLocaleString();

  return (
    <>
      <PageHeader
        title="Overview"
        description="System performance and key metrics"
      />

      <div className="grid grid-cols-1 md:grid-cols-12 gap-gutter mb-xl">
        <div className="md:col-span-4 flex flex-col gap-gutter">
          <StatsCard
            label="Calls Today"
            value={summary ? formatCalls(summary.callsToday) : "—"}
            subtext={summary ? `+${summary.callsChange}% vs yesterday` : undefined}
            subtextVariant="positive"
            icon={TrendingUp}
          />
          <StatsCard
            label="Cache Hit %"
            value={summary ? `${summary.cacheHitPercent}%` : "—"}
            subtext="Stable over 7 days"
            icon={MemoryStick}
          />
          <StatsCard
            label="Avg Response"
            value={summary ? `${summary.avgResponseMs}` : "—"}
            subtext={
              summary
                ? `+${summary.responseChangeMs}ms avg increase`
                : undefined
            }
            subtextVariant="negative"
            icon={Timer}
          />
        </div>
        <div className="md:col-span-8">
          <UsageChart data={usage} />
        </div>
      </div>

      <RecentActivity activities={activity} />
    </>
  );
}
