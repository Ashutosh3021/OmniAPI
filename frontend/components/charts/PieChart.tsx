"use client";

import {
  Cell,
  Pie,
  PieChart as RechartsPieChart,
  ResponsiveContainer,
  Tooltip,
} from "recharts";

const COLORS = ["#06B6D4", "#94A3B8"];

interface PieChartProps {
  data: { name: string; value: number }[];
  height?: number;
}

export function CachePieChart({ data, height = 220 }: PieChartProps) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <RechartsPieChart>
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          innerRadius={50}
          outerRadius={80}
          paddingAngle={2}
          dataKey="value"
        >
          {data.map((_, index) => (
            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
          ))}
        </Pie>
        <Tooltip formatter={(value) => `${String(value)}%`} />
      </RechartsPieChart>
    </ResponsiveContainer>
  );
}
