"use client";

import {
  Cell,
  Pie,
  PieChart as RechartsPieChart,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import { ChartTooltip } from "./LineChart";

const COLORS = ["var(--c-accent)", "var(--c-line-strong)"];

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
          innerRadius="62%"
          outerRadius="88%"
          paddingAngle={2}
          dataKey="value"
          stroke="none"
        >
          {data.map((_, index) => (
            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
          ))}
        </Pie>
        <Tooltip content={<ChartTooltip />} />
      </RechartsPieChart>
    </ResponsiveContainer>
  );
}
