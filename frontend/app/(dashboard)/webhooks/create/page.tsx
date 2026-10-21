import type { Metadata } from "next";
import { CreateWebhookForm } from "@/components/forms/CreateWebhookForm";
import { PageHeader } from "@/components/shared/PageHeader";

export const metadata: Metadata = {
  title: "Add a webhook",
  description:
    "Subscribe an HTTPS endpoint to an OmniAPI event. Every delivery is signed and retried on failure.",
};

export default function CreateWebhookPage() {
  return (
    <div className="max-w-xl">
      <PageHeader
        meta="signed deliveries"
        title="Add a webhook"
        description="OmniAPI pushes the event to your endpoint as soon as it happens, and retries a failed delivery with exponential backoff."
      />
      <div className="panel p-5 md:p-7">
        <CreateWebhookForm />
      </div>
    </div>
  );
}
