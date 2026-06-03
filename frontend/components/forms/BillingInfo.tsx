import { Card } from "@/components/shared/Card";
import { Badge } from "@/components/shared/Badge";

export function BillingInfo() {
  return (
    <Card className="max-w-lg">
      <div className="flex items-center justify-between mb-md">
        <h3 className="text-headline-sm font-semibold">Current Plan</h3>
        <Badge variant="info">Pro</Badge>
      </div>
      <p className="text-body-md text-on-surface-variant mb-lg">
        You are on the Pro plan with 5M API calls per month. Billing is managed through
        your organization admin.
      </p>
      <div className="grid grid-cols-2 gap-md text-body-sm">
        <div>
          <p className="text-on-surface-variant">Monthly cost</p>
          <p className="font-semibold text-on-surface">$99 / month</p>
        </div>
        <div>
          <p className="text-on-surface-variant">Next billing date</p>
          <p className="font-semibold text-on-surface">Jun 1, 2026</p>
        </div>
      </div>
      <button
        type="button"
        disabled
        className="mt-lg text-label-md text-on-surface-variant cursor-not-allowed"
      >
        Manage billing (coming soon)
      </button>
    </Card>
  );
}
