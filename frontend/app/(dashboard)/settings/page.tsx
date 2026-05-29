import { ProfileForm } from "@/components/forms/ProfileForm";
import { SecuritySettings } from "@/components/forms/SecuritySettings";
import { BillingInfo } from "@/components/forms/BillingInfo";
import { PageHeader } from "@/components/shared/PageHeader";
import { Card } from "@/components/shared/Card";

export default function SettingsPage() {
  return (
    <>
      <PageHeader
        title="Settings"
        description="Manage your profile, security, and billing"
      />

      <div className="space-y-xl max-w-3xl">
        <section>
          <h2 className="text-headline-sm font-semibold mb-md">Profile</h2>
          <Card>
            <ProfileForm />
          </Card>
        </section>

        <section>
          <h2 className="text-headline-sm font-semibold mb-md">Security</h2>
          <Card>
            <SecuritySettings />
          </Card>
        </section>

        <section>
          <h2 className="text-headline-sm font-semibold mb-md">Billing</h2>
          <BillingInfo />
        </section>
      </div>
    </>
  );
}
