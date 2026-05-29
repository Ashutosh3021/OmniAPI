import { CreateWebhookForm } from "@/components/forms/CreateWebhookForm";
import { PageHeader } from "@/components/shared/PageHeader";
import { Card } from "@/components/shared/Card";

export default function CreateWebhookPage() {
  return (
    <div className="max-w-2xl mx-auto">
      <PageHeader
        title="Create Webhook"
        description="Configure an endpoint to receive event notifications."
      />
      <Card>
        <CreateWebhookForm />
      </Card>
    </div>
  );
}
