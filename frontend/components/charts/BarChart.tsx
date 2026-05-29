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

interface BarChartProps {
  data: { endpoint: string; calls: number }[];
  height?: number;
}

export function EndpointBarChart({ data, height = 280 }: BarChartProps) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <RechartsBarChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#c6c6cd" />
        <XAxis dataKey="endpoint" tick={{ fontSize: 11 }} stroke="#94A3B8" />
        <YAxis tick={{ fontSize: 12 }} stroke="#94A3B8" />
        <Tooltip />
        <Bar dataKey="calls" fill="#06B6D4" radius={[2, 2, 0, 0]} />
      </RechartsBarChart>
    </ResponsiveContainer>
  );
}
