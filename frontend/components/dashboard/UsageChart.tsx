"use client";

import { useState } from "react";
import { UsageLineChart } from "@/components/charts/LineChart";
import type { UsageDataPoint } from "@/types";
import { cn } from "@/lib/utils";

const RANGES = ["1H", "24H", "7D"] as const;

interface UsageChartProps {
  data: UsageDataPoint[];
}

export function UsageChart({ data }: UsageChartProps) {
  const [range, setRange] = useState<(typeof RANGES)[number]>("24H");

  return (
    <div className="bg-white dark:bg-surface border border-outline rounded-xl p-lg flex flex-col min-h-[300px] md:min-h-[400px]">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-md mb-lg">
        <h3 className="text-headline-sm font-semibold text-on-surface">
          API Usage (Requests/sec)
        </h3>
        <div className="flex gap-sm">
          {RANGES.map((r) => (
            <button
              key={r}
              type="button"
              onClick={() => setRange(r)}
              className={cn(
                "px-sm py-xs border rounded text-label-sm transition-colors",
                range === r
                  ? "bg-surface-container-low border-secondary-fixed text-secondary-fixed"
                  : "border-outline text-on-surface-variant hover:border-secondary-fixed hover:text-secondary-fixed"
              )}
            >
              {r}
            </button>
          ))}
        </div>
      </div>
      <div className="flex-1 min-h-[200px] md:min-h-[280px]">
        <UsageLineChart data={data} height={280} />
      </div>
    </div>
  );
}
