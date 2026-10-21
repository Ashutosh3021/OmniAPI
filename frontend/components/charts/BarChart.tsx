"use client";

import {
  Bar,
  BarChart as RechartsBarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { ChartTooltip } from "./LineChart";

interface BarChartProps {
  data: { label: string; value: number }[];
  height?: number;
  /** Renders the bars horizontally, for long labels. */
  horizontal?: boolean;
}

export function VolumeBarChart({ data, height = 280 }: BarChartProps) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <RechartsBarChart
        data={data}
        margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
      >
        <CartesianGrid stroke="var(--c-line)" vertical={false} />
        <XAxis
          dataKey="label"
          tick={{ fontSize: 11, fill: "var(--c-muted)" }}
          tickLine={false}
          axisLine={{ stroke: "var(--c-line)" }}
          interval={0}
        />
        <YAxis
          tick={{ fontSize: 11, fill: "var(--c-muted)" }}
          tickLine={false}
          axisLine={false}
          width={46}
        />
        <Tooltip
          content={<ChartTooltip />}
          cursor={{ fill: "var(--c-ink-soft)" }}
        />
        <Bar
          dataKey="value"
          fill="var(--c-accent)"
          radius={[2, 2, 0, 0]}
          maxBarSize={40}
        />
      </RechartsBarChart>
    </ResponsiveContainer>
  );
}
