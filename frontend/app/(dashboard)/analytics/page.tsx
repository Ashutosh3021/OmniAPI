"use client";

import { useEffect, useState } from "react";
import {
  LineChart,
  Line,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  Legend,
} from "recharts";
import { PageHeader } from "@/components/shared/PageHeader";
import { Spinner } from "@/components/shared/Spinner";
import { Card } from "@/components/shared/Card";
import { UsageLineChart } from "@/components/charts/LineChart";
import { EndpointBarChart } from "@/components/charts/BarChart";
import { CachePieChart } from "@/components/charts/PieChart";
import { ExportReport } from "@/components/analytics/ExportReport";
import { api } from "@/lib/api";
import type { AnalyticsSummary, UsageDataPoint } from "@/types";

interface AnalyticsData {
  summary: AnalyticsSummary;
  usage: UsageDataPoint[];
  cache: { name: string; value: number }[];
  latency: { time: string; p50: number; p95: number }[];
  endpoints: { endpoint: string; calls: number }[];
}

export default function AnalyticsPage() {
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get<AnalyticsData>("/analytics").then(setData).finally(() => setLoading(false));
  }, []);

  if (loading) return <Spinner />;
  if (!data) return <p>Failed to load analytics</p>;

  const exportData = data.endpoints.map((e) => ({
    endpoint: e.endpoint,
    calls: e.calls,
    cacheHit: data.summary.cache_hit_percent,
  }));

  return (
    <>
      <PageHeader
        title="Analytics"
        description="Usage metrics, cache performance, and response times"
        action={<ExportReport data={exportData} />}
      />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-gutter mb-xl">
        <Card>
          <h3 className="text-headline-sm font-semibold mb-md">Request Volume</h3>
          <UsageLineChart data={data.usage} height={240} />
        </Card>
        <Card>
          <h3 className="text-headline-sm font-semibold mb-md">Cache Hit Rate</h3>
          <CachePieChart data={data.cache} />
          <p className="text-center text-display text-on-surface mt-sm">
            {data.summary.cache_hit_percent}%
          </p>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-gutter">
        <Card>
          <h3 className="text-headline-sm font-semibold mb-md">Response Latency (ms)</h3>
          <ResponsiveContainer width="100%" height={240}>
            <LineChart data={data.latency}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="p50" stroke="#06B6D4" name="p50" />
              <Line type="monotone" dataKey="p95" stroke="#00687a" name="p95" />
            </LineChart>
          </ResponsiveContainer>
        </Card>
        <Card>
          <h3 className="text-headline-sm font-semibold mb-md">Top Endpoints</h3>
          <EndpointBarChart data={data.endpoints} height={240} />
        </Card>
      </div>
    </>
  );
}
