"use client";

import { useState } from "react";
import { DOCS_SECTIONS } from "@/lib/constants";
import { PageHeader } from "@/components/shared/PageHeader";
import { cn } from "@/lib/utils";

const DOC_CONTENT: Record<string, { title: string; body: string; code?: string }> = {
  "getting-started": {
    title: "Getting Started",
    body: "OmniAPI is a unified gateway for managing external services, API keys, and webhooks. Install the SDK and authenticate with your API key.",
    code: `curl -H "Authorization: Bearer YOUR_API_KEY" \\
  https://api.omniapi.io/v1/health`,
  },
  authentication: {
    title: "Authentication",
    body: "All API requests require a Bearer token in the Authorization header. Create keys from the API Keys section with scoped permissions.",
    code: `const response = await fetch('/api/v1/users', {
  headers: { Authorization: \`Bearer \${API_KEY}\` }
});`,
  },
  "api-reference": {
    title: "API Reference",
    body: "Core endpoints include /api/v1/users, /api/v1/transactions, and /api/v1/products. Rate limits apply per key based on your plan.",
  },
  webhooks: {
    title: "Webhooks",
    body: "Configure webhook endpoints to receive signed POST payloads when events occur. Verify signatures using your webhook secret.",
    code: `// Verify webhook signature
const sig = request.headers['x-omni-signature'];
const valid = verifySignature(payload, sig, WEBHOOK_SECRET);`,
  },
  "code-examples": {
    title: "Code Examples",
    body: "Use the Orchestrate playground to test requests interactively, or integrate with our Node.js and Python SDKs.",
    code: `import { OmniClient } from '@omniapi/sdk';

const client = new OmniClient({ apiKey: process.env.OMNI_API_KEY });
const data = await client.users.list();`,
  },
};

export default function DocsPage() {
  const [active, setActive] = useState<string>(DOCS_SECTIONS[0].id);
  const content = DOC_CONTENT[active];

  return (
    <div className="flex flex-col lg:flex-row gap-gutter">
      <aside className="lg:w-64 shrink-0">
        <PageHeader title="Documentation" description="Guides and API reference" className="lg:hidden" />
        <nav className="sticky top-4 bg-white dark:bg-surface border border-outline rounded-xl p-md" aria-label="Documentation sections">
          <p className="text-label-sm text-on-surface-variant uppercase tracking-wider mb-sm hidden lg:block">
            Sections
          </p>
          <ul className="flex lg:flex-col gap-xs overflow-x-auto lg:overflow-visible pb-sm lg:pb-0">
            {DOCS_SECTIONS.map((section) => (
              <li key={section.id} className="shrink-0">
                <button
                  type="button"
                  onClick={() => setActive(section.id)}
                  className={cn(
                    "w-full text-left px-md py-sm rounded text-label-md whitespace-nowrap transition-colors",
                    active === section.id
                      ? "bg-surface-container-low text-secondary-fixed font-medium"
                      : "text-on-surface-variant hover:bg-surface-container-low"
                  )}
                >
                  {section.title}
                </button>
              </li>
            ))}
          </ul>
        </nav>
      </aside>

      <article className="flex-1 min-w-0">
        <div className="hidden lg:block mb-xl">
          <PageHeader title="Documentation" description="Guides and API reference" />
        </div>
        <div className="bg-white dark:bg-surface border border-outline rounded-xl p-lg md:p-xl">
          <h2 className="text-headline-md font-semibold text-on-surface mb-md">
            {content.title}
          </h2>
          <p className="text-body-md text-on-surface-variant mb-lg">{content.body}</p>
          {content.code && (
            <pre className="bg-slate-800 text-gray-300 p-md rounded-lg overflow-x-auto font-mono text-code text-sm custom-scrollbar">
              <code>{content.code}</code>
            </pre>
          )}
        </div>
      </article>
    </div>
  );
}
