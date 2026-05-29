import { ActivityTable } from "@/components/tables/ActivityTable";
import type { ActivityLog } from "@/types";

interface RecentActivityProps {
  activities: ActivityLog[];
}

export function RecentActivity({ activities }: RecentActivityProps) {
  return (
    <div className="bg-white dark:bg-surface border border-outline rounded-xl overflow-hidden">
      <div className="p-lg border-b border-outline flex justify-between items-center">
        <h3 className="text-headline-sm font-semibold text-on-surface">Recent Activity</h3>
        <button type="button" className="text-secondary-fixed text-label-sm hover:underline">
          View All Logs
        </button>
      </div>
      <ActivityTable activities={activities} />
    </div>
  );
}
