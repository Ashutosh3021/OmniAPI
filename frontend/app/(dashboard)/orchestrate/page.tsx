import type { Metadata } from "next";
import { APIPlayground } from "@/components/orchestrate/APIPlayground";
import { PageHeader } from "@/components/shared/PageHeader";

export const metadata: Metadata = {
  title: "Orchestrate",
  description:
    "Build a request, run it against the live gateway and watch every branch of the fan answer.",
};

export default function OrchestratePage() {
  return (
    <>
      <PageHeader
        meta="live gateway"
        title="Orchestrate"
        description="Pick the services you need, send one request, and watch every branch answer on its own."
      />
      <APIPlayground />
    </>
  );
}
