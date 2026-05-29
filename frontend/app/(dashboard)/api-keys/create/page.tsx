import { CreateAPIKeyForm } from "@/components/forms/CreateAPIKeyForm";
import { PageHeader } from "@/components/shared/PageHeader";
import { Card } from "@/components/shared/Card";

export default function CreateApiKeyPage() {
  return (
    <div className="max-w-3xl mx-auto">
      <PageHeader
        title="Create API Key"
        description="Generate a new key to authenticate requests from your external applications to OmniAPI."
      />
      <Card>
        <CreateAPIKeyForm />
      </Card>
    </div>
  );
}
