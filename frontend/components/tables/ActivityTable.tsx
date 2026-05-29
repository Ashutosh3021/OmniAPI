import { Badge } from "@/components/shared/Badge";
import { formatRelativeTime } from "@/lib/utils";
import type { ActivityLog } from "@/types";

interface ActivityTableProps {
  activities: ActivityLog[];
}

function statusVariant(status: number): "success" | "error" | "info" {
  if (status >= 200 && status < 300) return "success";
  if (status >= 400) return "error";
  return "info";
}

export function ActivityTable({ activities }: ActivityTableProps) {
  return (
    <>
      <div className="hidden md:block overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-surface-container-low border-b border-outline">
              <th className="py-sm px-lg text-label-sm text-on-surface-variant uppercase font-semibold">Status</th>
              <th className="py-sm px-lg text-label-sm text-on-surface-variant uppercase font-semibold">Method</th>
              <th className="py-sm px-lg text-label-sm text-on-surface-variant uppercase font-semibold">Endpoint</th>
              <th className="py-sm px-lg text-label-sm text-on-surface-variant uppercase font-semibold">Latency</th>
              <th className="py-sm px-lg text-label-sm text-on-surface-variant uppercase font-semibold">Time</th>
            </tr>
          </thead>
          <tbody className="font-mono text-code">
            {activities.map((act) => (
              <tr key={act.id} className="border-b border-outline-variant hover:bg-surface-container-low">
                <td className="py-md px-lg">
                  <Badge variant={statusVariant(act.status)}>{act.statusLabel}</Badge>
                </td>
                <td className={`py-md px-lg ${act.method === "POST" ? "text-secondary-fixed" : "text-on-surface"}`}>
                  {act.method}
                </td>
                <td className="py-md px-lg text-on-surface-variant">{act.endpoint}</td>
                <td className="py-md px-lg text-on-surface">{act.latency}ms</td>
                <td className="py-md px-lg text-on-surface-variant font-sans text-body-sm">
                  {formatRelativeTime(act.timestamp)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="md:hidden divide-y divide-outline-variant">
        {activities.map((act) => (
          <div key={act.id} className="py-md px-md">
            <div className="flex items-center gap-sm mb-xs">
              <Badge variant={statusVariant(act.status)}>{act.statusLabel}</Badge>
              <span className="font-mono text-code">{act.method}</span>
            </div>
            <p className="font-mono text-code text-on-surface-variant text-body-sm truncate">{act.endpoint}</p>
            <p className="text-label-sm text-on-surface-variant mt-xs">
              {act.latency}ms · {formatRelativeTime(act.timestamp)}
            </p>
          </div>
        ))}
      </div>
    </>
  );
}
