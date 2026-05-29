import { CreateExternalServiceForm } from "@/components/forms/CreateExternalServiceForm";
import { PageHeader } from "@/components/shared/PageHeader";
import { Card } from "@/components/shared/Card";

export default function CreateExternalServicePage() {
  return (
    <div className="max-w-2xl mx-auto">
      <PageHeader
        title="Add External Service"
        description="Connect a third-party provider to your OmniAPI workspace."
      />
      <Card>
        <CreateExternalServiceForm />
      </Card>
    </div>
  );
}
