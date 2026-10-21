import type { Metadata } from "next";
import { CreateAPIKeyForm } from "@/components/forms/CreateAPIKeyForm";
import { PageHeader } from "@/components/shared/PageHeader";

export const metadata: Metadata = {
  title: "Create an API key",
  description:
    "Mint an OmniAPI key for your application, with an optional expiry date. The raw key is shown once.",
};

export default function CreateApiKeyPage() {
  return (
    <div className="max-w-xl">
      <PageHeader
        meta="shown once"
        title="Create an API key"
        description="One key per application. It carries the permissions you need and is sent in the X-API-Key header."
      />
      <div className="panel p-5 md:p-7">
        <CreateAPIKeyForm />
      </div>
    </div>
  );
}
