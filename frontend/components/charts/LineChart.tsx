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

interface LineChartProps {
  data: { time: string; requests: number }[];
  height?: number;
}

export function UsageLineChart({ data, height = 300 }: LineChartProps) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
        <defs>
          <linearGradient id="usageGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#06B6D4" stopOpacity={0.3} />
            <stop offset="95%" stopColor="#06B6D4" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="#c6c6cd" />
        <XAxis dataKey="time" tick={{ fontSize: 12 }} stroke="#94A3B8" />
        <YAxis tick={{ fontSize: 12 }} stroke="#94A3B8" />
        <Tooltip
          contentStyle={{
            background: "#fff",
            border: "1px solid #94A3B8",
            borderRadius: "4px",
            fontSize: "12px",
          }}
        />
        <Area
          type="monotone"
          dataKey="requests"
          stroke="#06B6D4"
          strokeWidth={2}
          fill="url(#usageGradient)"
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
