import type { Metadata } from "next";
import { SiteHeader } from "@/components/shell/SiteHeader";
import { SiteFooter } from "@/components/shell/SiteFooter";

export const metadata: Metadata = {
  title: "Documentation",
  description:
    "How to call OmniAPI: authentication, external services, parallel orchestration, webhooks and the full API reference.",
  alternates: { canonical: "/docs" },
};

export default function DocsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <>
      <SiteHeader />
      <main id="main" tabIndex={-1}>
        {children}
      </main>
      <SiteFooter />
    </>
  );
}
