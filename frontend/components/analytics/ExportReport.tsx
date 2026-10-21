"use client";

import { useState } from "react";
import { Download } from "lucide-react";
import { Button } from "@/components/shared/Button";
import { API_BASE } from "@/lib/constants";
import { getStoredToken } from "@/lib/auth";
import { downloadBlob, downloadFile } from "@/lib/utils";

interface ExportReportProps {
  data: Record<string, unknown>[];
}

export function ExportReport({ data }: ExportReportProps) {
  const [busy, setBusy] = useState(false);

  const downloadCsv = async () => {
    setBusy(true);
    try {
      const token = getStoredToken();
      const response = await fetch(`${API_BASE}/analytics/reports`, {
        headers: token ? { Authorization: `Bearer ${token}` } : undefined,
      });
      if (!response.ok) throw new Error("Report download failed");
      const blob = await response.blob();
      downloadBlob(blob, "omniapi-usage-report.csv");
    } catch {
      // The button stays available; a failed download simply does not start.
    } finally {
      setBusy(false);
    }
  };

  const downloadJson = () => {
    downloadFile(
      JSON.stringify(data, null, 2),
      "omniapi-analytics.json",
      "application/json"
    );
  };

  return (
    <div className="flex flex-wrap items-center gap-2">
      <Button
        variant="secondary"
        size="sm"
        onClick={downloadCsv}
        loading={busy}
        disabled={data.length === 0}
      >
        <Download className="h-3.5 w-3.5" aria-hidden />
        CSV report
      </Button>
      <Button
        variant="secondary"
        size="sm"
        onClick={downloadJson}
        disabled={data.length === 0}
      >
        <Download className="h-3.5 w-3.5" aria-hidden />
        JSON
      </Button>
    </div>
  );
}
