import { APIPlayground } from "@/components/orchestrate/APIPlayground";
import { PageHeader } from "@/components/shared/PageHeader";

export default function OrchestratePage() {
  return (
    <>
      <PageHeader
        title="Orchestrate"
        description="Test and debug API requests in the playground"
      />
      <APIPlayground />
    </>
  );
}
