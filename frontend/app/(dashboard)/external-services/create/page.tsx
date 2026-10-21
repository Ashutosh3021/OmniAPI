import type { Metadata } from "next";
import { CreateExternalServiceForm } from "@/components/forms/CreateExternalServiceForm";
import { PageHeader } from "@/components/shared/PageHeader";

export const metadata: Metadata = {
  title: "Connect a provider",
  description:
    "Register a third-party provider key. OmniAPI encrypts it and calls the provider on your behalf.",
};

export default function CreateExternalServicePage() {
  return (
    <div className="max-w-xl">
      <PageHeader
        meta="encrypted at rest"
        title="Connect a provider"
        description="A connected provider becomes a branch you can call from the orchestrate endpoint."
      />
      <div className="panel p-5 md:p-7">
        <CreateExternalServiceForm />
      </div>
    </div>
  );
}
