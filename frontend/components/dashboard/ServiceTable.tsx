import { cn } from "@/lib/utils";

/** Mirrors the backend ServiceBreakdown. */
export interface ServiceRow {
  service_name: string;
  call_count: number;
  cache_hits: number;
  avg_response_time_ms: number;
  error_count: number;
}

interface ServiceTableProps {
  rows: ServiceRow[];
  className?: string;
}

/** The per-service breakdown. Real numbers only, straight from the analytics API. */
export function ServiceTable({ rows, className }: ServiceTableProps) {
  if (rows.length === 0) {
    return (
      <p className="py-8 text-center text-ui text-muted">
        No calls recorded for this period yet.
      </p>
    );
  }

  return (
    <div className={cn("overflow-x-auto", className)}>
      <table className="data-table">
        <thead>
          <tr>
            <th scope="col">Service</th>
            <th scope="col" className="text-right">
              Calls
            </th>
            <th scope="col" className="text-right">
              Cached
            </th>
            <th scope="col" className="text-right">
              Avg response
            </th>
            <th scope="col" className="text-right">
              Errors
            </th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => {
            const cacheRate = row.call_count
              ? Math.round((row.cache_hits / row.call_count) * 100)
              : 0;
            return (
              <tr key={row.service_name}>
                <td className="font-medium text-ink">{row.service_name}</td>
                <td className="text-right num text-muted">
                  {row.call_count.toLocaleString()}
                </td>
                <td className="text-right num text-muted">{cacheRate}%</td>
                <td className="text-right num text-muted">
                  {Math.round(row.avg_response_time_ms)} ms
                </td>
                <td
                  className={cn(
                    "text-right num",
                    row.error_count > 0 ? "text-bad" : "text-muted"
                  )}
                >
                  {row.error_count}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
