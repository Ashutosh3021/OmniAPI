"use client";

import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

interface TooltipItem {
  name?: string | number;
  value?: number | string;
}

interface ChartTooltipProps {
  active?: boolean;
  payload?: TooltipItem[];
  label?: string | number;
}

export function ChartTooltip({ active, payload, label }: ChartTooltipProps) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded border border-ink/15 bg-surface px-2.5 py-1.5 shadow-lg">
      {label !== undefined && (
        <p className="font-mono text-micro text-muted">{label}</p>
      )}
      {payload.map((item, i) => (
        <p key={i} className="font-mono text-micro text-ink num">
          {item.value}
        </p>
      ))}
    </div>
  );
}

interface LineChartProps {
  data: { time: string; requests: number }[];
  height?: number;
}

export function UsageLineChart({ data, height = 300 }: LineChartProps) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
        <defs>
          <linearGradient id="usageFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="var(--c-accent)" stopOpacity={0.24} />
            <stop offset="100%" stopColor="var(--c-accent)" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid stroke="var(--c-line)" vertical={false} />
        <XAxis
          dataKey="time"
          tick={{ fontSize: 11, fill: "var(--c-muted)" }}
          tickLine={false}
          axisLine={{ stroke: "var(--c-line)" }}
          interval="preserveStartEnd"
        />
        <YAxis
          tick={{ fontSize: 11, fill: "var(--c-muted)" }}
          tickLine={false}
          axisLine={false}
          width={46}
        />
        <Tooltip
          content={<ChartTooltip />}
          cursor={{ stroke: "var(--c-line-strong)" }}
        />
        <Area
          type="monotone"
          dataKey="requests"
          stroke="var(--c-accent)"
          strokeWidth={1.75}
          fill="url(#usageFill)"
          dot={false}
          activeDot={{
            r: 3.5,
            fill: "var(--c-accent)",
            stroke: "var(--c-surface)",
            strokeWidth: 2,
          }}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
