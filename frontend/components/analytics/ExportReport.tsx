"use client";

import { Download } from "lucide-react";
import { Button } from "@/components/shared/Button";
import { downloadFile } from "@/lib/utils";

interface ExportReportProps {
  data: Record<string, unknown>[];
}

export function ExportReport({ data }: ExportReportProps) {
  const exportCsv = () => {
    if (data.length === 0) return;
    const headers = Object.keys(data[0]);
    const rows = data.map((row) =>
      headers.map((h) => JSON.stringify(row[h] ?? "")).join(",")
    );
    const csv = [headers.join(","), ...rows].join("\n");
    downloadFile(csv, "omniapi-analytics.csv", "text/csv");
  };

  const exportJson = () => {
    downloadFile(JSON.stringify(data, null, 2), "omniapi-analytics.json", "application/json");
  };

  return (
    <div className="flex flex-wrap gap-sm">
      <Button variant="outline" onClick={exportCsv}>
        <Download className="h-4 w-4" />
        Export CSV
      </Button>
      <Button variant="outline" onClick={exportJson}>
        <Download className="h-4 w-4" />
        Export JSON
      </Button>
    </div>
  );
}
