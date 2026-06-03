"use client";

import { useState } from "react";
import Link from "next/link";
import { ExternalLink } from "lucide-react";
import { DOCS_SECTIONS } from "@/lib/constants";
import { PageHeader } from "@/components/shared/PageHeader";
import { CopyButton } from "@/components/shared/CopyButton";
import { Badge } from "@/components/shared/Badge";
import { cn } from "@/lib/utils";

/* ─── helper: code block with copy button ───────────────────────────── */
function CodeBlock({ code, language = "bash" }: { code: string; language?: string }) {
  return (
    <div className="relative group rounded-lg overflow-hidden mt-md mb-lg">
      <div className="flex items-center justify-between bg-slate-900 px-md py-xs border-b border-slate-700">
        <span className="text-xs text-slate-400 font-mono">{language}</span>
        <CopyButton value={code} />
      </div>
      <pre className="bg-slate-800 text-gray-200 p-md overflow-x-auto font-mono text-sm leading-relaxed custom-scrollbar">
        <code>{code}</code>
      </pre>
    </div>
  );
}

/* ─── helper: info callout ───────────────────────────────────────────── */
function Callout({
  type = "info",
  children,
}: {
  type?: "info" | "warning" | "tip";
  children: React.ReactNode;
}) {
  const styles = {
    info: "bg-blue-50 dark:bg-blue-950/30 border-blue-200 dark:border-blue-800 text-blue-900 dark:text-blue-200",
    warning: "bg-amber-50 dark:bg-amber-950/30 border-amber-200 dark:border-amber-800 text-amber-900 dark:text-amber-200",
    tip: "bg-emerald-50 dark:bg-emerald-950/30 border-emerald-200 dark:border-emerald-800 text-emerald-900 dark:text-emerald-200",
  };
  const labels = { info: "ℹ️ Note", warning: "⚠️ Important", tip: "✅ Tip" };
  return (
    <div className={cn("border rounded-lg p-md mb-lg text-body-sm", styles[type])}>
      <span className="font-semibold mr-sm">{labels[type]}</span>
      {children}
    </div>
  );
}

/* ─── helper: step badge ─────────────────────────────────────────────── */
function Step({ n, title }: { n: number; title: string }) {
  return (
    <div className="flex items-center gap-md mt-xl mb-md">
      <span className="flex-shrink-0 w-8 h-8 rounded-full bg-secondary-fixed text-on-secondary-fixed flex items-center justify-center text-label-md font-bold">
        {n}
      </span>
      <h3 className="text-headline-sm font-semibold text-on-surface">{title}</h3>
    </div>
  );
}

/* ─── helper: endpoint row ───────────────────────────────────────────── */
function Endpoint({
  method,
  path,
  description,
}: {
  method: string;
  path: string;
  description: string;
}) {
  const methodColors: Record<string, string> = {
    GET: "bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-300",
    POST: "bg-green-100 text-green-800 dark:bg-green-900/40 dark:text-green-300",
    PATCH: "bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300",
    DELETE: "bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-300",
  };
  return (
    <div className="flex flex-col sm:flex-row sm:items-center gap-sm py-sm border-b border-outline-variant last:border-0">
      <span
        className={cn(
          "shrink-0 inline-block px-sm py-xs rounded font-mono text-xs font-bold w-16 text-center",
          methodColors[method] ?? "bg-surface-container text-on-surface"
        )}
      >
        {method}
      </span>
      <code className="font-mono text-sm text-secondary-fixed shrink-0">{path}</code>
      <span className="text-body-sm text-on-surface-variant">{description}</span>
    </div>
  );
}

/* ─── section content ────────────────────────────────────────────────── */
function GettingStarted() {
  return (
    <div>
      <p className="text-body-md text-on-surface-variant mb-lg">
        OmniAPI is a unified gateway that lets your application call multiple external APIs
        (weather, news, stock data, and more) through a <strong>single endpoint</strong> using
        a single key. It handles caching, rate limiting, parallel fetching, and retries for
        you automatically.
      </p>

      <h3 className="text-headline-sm font-semibold mb-md">How it works in 4 steps</h3>
      <ol className="space-y-sm text-body-md text-on-surface-variant list-none mb-xl">
        {[
          "Create an OmniAPI account and log in.",
          "Go to External Services and add your API keys for each provider (e.g. OpenWeatherMap, NewsAPI).",
          "Go to API Keys and generate an OmniAPI key for your application.",
          "Use that OmniAPI key to call POST /api/v1/orchestrate, telling it which services to call.",
        ].map((step, i) => (
          <li key={i} className="flex gap-md">
            <span className="flex-shrink-0 w-6 h-6 rounded-full bg-surface-container-low border border-outline text-label-sm font-bold flex items-center justify-center text-on-surface-variant">
              {i + 1}
            </span>
            <span>{step}</span>
          </li>
        ))}
      </ol>

      <Callout type="tip">
        The live API is at{" "}
        <code className="font-mono text-sm">https://omniapi-api.onrender.com/api/v1</code>.
        Interactive API docs (Swagger UI) are available at{" "}
        <a
          href="https://omniapi-api.onrender.com/docs"
          target="_blank"
          rel="noopener noreferrer"
          className="underline inline-flex items-center gap-xs"
        >
          omniapi-api.onrender.com/docs <ExternalLink className="h-3 w-3" />
        </a>
      </Callout>

      <h3 className="text-headline-sm font-semibold mb-sm">Quick health check</h3>
      <CodeBlock language="bash" code={`curl https://omniapi-api.onrender.com/api/v1/health`} />
    </div>
  );
}

function Authentication() {
  return (
    <div>
      <p className="text-body-md text-on-surface-variant mb-lg">
        OmniAPI uses two types of credentials depending on who is making the request.
      </p>

      <h3 className="text-headline-sm font-semibold mb-md">1 — JWT Bearer token (dashboard / trusted servers)</h3>
      <p className="text-body-sm text-on-surface-variant mb-sm">
        When you log in via the dashboard or the <code className="font-mono">/auth/login</code>{" "}
        endpoint, you receive an <strong>access token</strong> and a{" "}
        <strong>refresh token</strong>. Pass the access token in the{" "}
        <code className="font-mono">Authorization</code> header.
      </p>
      <CodeBlock language="bash" code={`# 1. Log in
curl -X POST https://omniapi-api.onrender.com/api/v1/auth/login \\
  -H "Content-Type: application/json" \\
  -d '{"email":"you@example.com","password":"yourpassword"}'

# Response
# { "access_token": "eyJ...", "refresh_token": "eyJ..." }

# 2. Use the token
curl https://omniapi-api.onrender.com/api/v1/api-keys \\
  -H "Authorization: Bearer eyJ..."`} />

      <Callout type="info">
        Access tokens expire. When they do, call{" "}
        <code className="font-mono">POST /auth/refresh</code> with your{" "}
        <code className="font-mono">refresh_token</code> to get a new pair. The dashboard
        does this automatically.
      </Callout>

      <h3 className="text-headline-sm font-semibold mb-md mt-xl">2 — OmniAPI key (your application)</h3>
      <p className="text-body-sm text-on-surface-variant mb-sm">
        For your application code, generate an OmniAPI key from the{" "}
        <Link href="/api-keys" className="text-secondary-fixed underline">
          API Keys
        </Link>{" "}
        page. Pass it in the <code className="font-mono">X-API-Key</code> header.
      </p>
      <CodeBlock language="bash" code={`curl -X POST https://omniapi-api.onrender.com/api/v1/orchestrate \\
  -H "X-API-Key: omni_xK9mP2qL..." \\
  -H "Content-Type: application/json" \\
  -d '{"services":["weather"],"params":{"weather":{"city":"London"}}}'`} />

      <Callout type="warning">
        Your OmniAPI key is shown <strong>only once</strong> when created. Store it in an
        environment variable immediately — it cannot be retrieved again. If you lose it,
        delete it and generate a new one.
      </Callout>
    </div>
  );
}

function ExternalServices() {
  return (
    <div>
      <p className="text-body-md text-on-surface-variant mb-lg">
        Before you can orchestrate a service, you must register your API key for that provider
        under <strong>External Services</strong>. OmniAPI stores it encrypted and uses it on
        your behalf — your provider key is never exposed in any response.
      </p>

      <h3 className="text-headline-sm font-semibold mb-md">Supported services</h3>
      <div className="overflow-x-auto mb-xl">
        <table className="w-full text-body-sm border-collapse">
          <thead>
            <tr className="bg-surface-container-low border-b border-outline">
              <th className="text-left py-sm px-md text-label-sm text-on-surface-variant uppercase font-semibold">service_name</th>
              <th className="text-left py-sm px-md text-label-sm text-on-surface-variant uppercase font-semibold">Provider</th>
              <th className="text-left py-sm px-md text-label-sm text-on-surface-variant uppercase font-semibold">Where to get a key</th>
            </tr>
          </thead>
          <tbody>
            {[
              ["weather", "OpenWeatherMap", "openweathermap.org/api"],
              ["news", "NewsAPI", "newsapi.org"],
              ["stock", "Stock data provider", "your provider's dashboard"],
            ].map(([name, provider, link]) => (
              <tr key={name} className="border-b border-outline-variant">
                <td className="py-sm px-md"><code className="font-mono text-secondary-fixed">{name}</code></td>
                <td className="py-sm px-md text-on-surface-variant">{provider}</td>
                <td className="py-sm px-md text-on-surface-variant font-mono text-xs">{link}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <Step n={1} title="Add a service" />
      <CodeBlock language="bash" code={`curl -X POST https://omniapi-api.onrender.com/api/v1/external-services \\
  -H "Authorization: Bearer <your_jwt>" \\
  -H "Content-Type: application/json" \\
  -d '{
    "service_name": "weather",
    "api_key": "your_openweathermap_api_key",
    "max_calls_per_hour": 100
  }'`} />

      <Step n={2} title="List your services" />
      <CodeBlock language="bash" code={`curl https://omniapi-api.onrender.com/api/v1/external-services \\
  -H "Authorization: Bearer <your_jwt>"`} />
      <CodeBlock language="json" code={`[
  { "service_id": 1, "service_name": "weather", "max_calls_per_hour": 100, "status": "active" },
  { "service_id": 2, "service_name": "news",    "max_calls_per_hour": 60,  "status": "active" },
  { "service_id": 3, "service_name": "stock",   "max_calls_per_hour": 50,  "status": "active" }
]`} />

      <Step n={3} title="Update or remove a service" />
      <CodeBlock language="bash" code={`# Pause a service (stops orchestration without deleting the key)
curl -X PATCH https://omniapi-api.onrender.com/api/v1/external-services/1 \\
  -H "Authorization: Bearer <your_jwt>" \\
  -H "Content-Type: application/json" \\
  -d '{"status": "inactive"}'

# Remove permanently
curl -X DELETE https://omniapi-api.onrender.com/api/v1/external-services/1 \\
  -H "Authorization: Bearer <your_jwt>"`} />
    </div>
  );
}

function OrchestrateSection() {
  return (
    <div>
      <p className="text-body-md text-on-surface-variant mb-lg">
        The <code className="font-mono text-sm">/orchestrate</code> endpoint is the core of
        OmniAPI. You send one request listing which services you want, and OmniAPI calls them
        in parallel, caches the results, and returns everything together.
      </p>

      {/* ── How the services array works ── */}
      <h3 className="text-headline-sm font-semibold mb-md">
        Calling one specific service
      </h3>
      <p className="text-body-sm text-on-surface-variant mb-md">
        Say you have three external services configured — <Badge variant="info">weather</Badge>{" "}
        <Badge variant="info">news</Badge> <Badge variant="info">stock</Badge> — but right now
        you only want stock data. You simply put just{" "}
        <code className="font-mono text-sm">"stock"</code> in the{" "}
        <code className="font-mono text-sm">services</code> array. OmniAPI will only call that
        one service and ignore the others entirely.
      </p>
      <CodeBlock language="bash" code={`# Only call the "stock" service — weather and news are ignored
curl -X POST https://omniapi-api.onrender.com/api/v1/orchestrate \\
  -H "X-API-Key: omni_xK9mP2qL..." \\
  -H "Content-Type: application/json" \\
  -d '{
    "services": ["stock"],
    "params": {
      "stock": { "symbol": "AAPL" }
    }
  }'`} />
      <Callout type="tip">
        The <code className="font-mono">services</code> array controls which services are
        called for <em>this request</em>. Having other services configured in your account
        does not affect the call at all.
      </Callout>

      {/* ── Real example: A, B, C scenario ── */}
      <h3 className="text-headline-sm font-semibold mt-xl mb-md">
        Example: you have 3 services — call only one
      </h3>
      <p className="text-body-sm text-on-surface-variant mb-sm">
        Imagine your account has these three external services registered:
      </p>
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-sm mb-lg">
        {[
          { label: "Service A", name: "weather", color: "bg-blue-100 dark:bg-blue-900/30 border-blue-200 dark:border-blue-700" },
          { label: "Service B", name: "news",    color: "bg-purple-100 dark:bg-purple-900/30 border-purple-200 dark:border-purple-700" },
          { label: "Service C", name: "stock",   color: "bg-emerald-100 dark:bg-emerald-900/30 border-emerald-200 dark:border-emerald-700" },
        ].map(({ label, name, color }) => (
          <div key={name} className={cn("rounded-lg border p-md text-center", color)}>
            <p className="text-label-sm font-semibold text-on-surface">{label}</p>
            <code className="text-xs font-mono text-on-surface-variant">{name}</code>
          </div>
        ))}
      </div>
      <p className="text-body-sm text-on-surface-variant mb-sm">
        You want to call <strong>only Service C (stock)</strong>. Here is the exact request:
      </p>
      <CodeBlock language="bash" code={`curl -X POST https://omniapi-api.onrender.com/api/v1/orchestrate \\
  -H "X-API-Key: omni_xK9mP2qL..." \\
  -H "Content-Type: application/json" \\
  -d '{
    "services": ["stock"],
    "params": {
      "stock": { "symbol": "TSLA" }
    }
  }'`} />
      <CodeBlock language="json" code={`{
  "request_id": "a1b2c3d4-e5f6-...",
  "total_time_ms": 245,
  "timestamp": "2026-06-03T10:00:00Z",
  "results": [
    {
      "service": "stock",
      "success": true,
      "cache_hit": false,
      "response_time_ms": 243,
      "data": {
        "symbol": "TSLA",
        "price": 182.50,
        "change_percent": 1.2
      }
    }
  ]
}`} />
      <p className="text-body-sm text-on-surface-variant mb-sm">
        To call <strong>only Service B (news)</strong> instead:
      </p>
      <CodeBlock language="bash" code={`curl -X POST https://omniapi-api.onrender.com/api/v1/orchestrate \\
  -H "X-API-Key: omni_xK9mP2qL..." \\
  -H "Content-Type: application/json" \\
  -d '{
    "services": ["news"],
    "params": {
      "news": { "q": "electric vehicles", "pageSize": 5 }
    }
  }'`} />

      {/* ── Calling multiple at once ── */}
      <h3 className="text-headline-sm font-semibold mt-xl mb-md">
        Calling multiple services in one shot
      </h3>
      <p className="text-body-sm text-on-surface-variant mb-sm">
        Add multiple names to <code className="font-mono">services</code>. OmniAPI calls them
        all in parallel and returns results together. Each service gets its own entry in{" "}
        <code className="font-mono">results</code>.
      </p>
      <CodeBlock language="bash" code={`curl -X POST https://omniapi-api.onrender.com/api/v1/orchestrate \\
  -H "X-API-Key: omni_xK9mP2qL..." \\
  -H "Content-Type: application/json" \\
  -d '{
    "services": ["weather", "news", "stock"],
    "params": {
      "weather": { "city": "New York" },
      "news":    { "q": "AI", "pageSize": 3 },
      "stock":   { "symbol": "NVDA" }
    }
  }'`} />

      {/* ── cache_hit explained ── */}
      <h3 className="text-headline-sm font-semibold mt-xl mb-md">Understanding cache_hit</h3>
      <p className="text-body-sm text-on-surface-variant mb-sm">
        Each result has a <code className="font-mono">cache_hit</code> field:
      </p>
      <div className="space-y-sm mb-lg">
        <div className="flex gap-md p-sm rounded-lg bg-surface-container-low border border-outline">
          <Badge variant="success">true</Badge>
          <span className="text-body-sm text-on-surface-variant">
            Data was served from Redis. <code className="font-mono">response_time_ms</code> will
            be <code className="font-mono">0</code>. No call was made to the external provider —
            saves your quota.
          </span>
        </div>
        <div className="flex gap-md p-sm rounded-lg bg-surface-container-low border border-outline">
          <Badge variant="error">false</Badge>
          <span className="text-body-sm text-on-surface-variant">
            Fresh data was fetched from the provider via a background Celery task and then
            cached for future requests.
          </span>
        </div>
      </div>

      {/* ── Rate limits ── */}
      <h3 className="text-headline-sm font-semibold mt-xl mb-md">Rate limit headers</h3>
      <p className="text-body-sm text-on-surface-variant mb-sm">
        Every orchestrate response includes these headers so your application can back off
        before hitting the limit:
      </p>
      <CodeBlock language="http" code={`X-RateLimit-Limit: 100
X-RateLimit-Remaining: 73`} />
    </div>
  );
}

function ApiReference() {
  return (
    <div>
      <p className="text-body-md text-on-surface-variant mb-lg">
        All endpoints are under{" "}
        <code className="font-mono text-sm">https://omniapi-api.onrender.com/api/v1</code>.
        Interactive Swagger docs are at{" "}
        <a
          href="https://omniapi-api.onrender.com/docs"
          target="_blank"
          rel="noopener noreferrer"
          className="text-secondary-fixed underline inline-flex items-center gap-xs"
        >
          /docs <ExternalLink className="h-3 w-3" />
        </a>.
      </p>

      {[
        {
          group: "Auth",
          endpoints: [
            { method: "POST", path: "/auth/register", description: "Create a new account" },
            { method: "POST", path: "/auth/login", description: "Get access + refresh token pair" },
            { method: "POST", path: "/auth/refresh", description: "Rotate tokens using a refresh token" },
            { method: "GET",  path: "/auth/me", description: "Return the current authenticated user" },
          ],
        },
        {
          group: "API Keys",
          endpoints: [
            { method: "POST",   path: "/api-keys", description: "Create a new OmniAPI key (raw key shown once)" },
            { method: "GET",    path: "/api-keys", description: "List all your API keys" },
            { method: "GET",    path: "/api-keys/{key_id}", description: "Get a single key by ID" },
            { method: "PATCH",  path: "/api-keys/{key_id}", description: "Update name or expiry date" },
            { method: "DELETE", path: "/api-keys/{key_id}", description: "Permanently delete a key" },
          ],
        },
        {
          group: "External Services",
          endpoints: [
            { method: "POST",   path: "/external-services", description: "Register an external service API key" },
            { method: "GET",    path: "/external-services", description: "List all configured services" },
            { method: "GET",    path: "/external-services/{id}", description: "Get one service" },
            { method: "PATCH",  path: "/external-services/{id}", description: "Update key, rate limit, or status" },
            { method: "DELETE", path: "/external-services/{id}", description: "Remove a service" },
          ],
        },
        {
          group: "Orchestrate",
          endpoints: [
            { method: "POST", path: "/orchestrate", description: "Call one or more services in parallel" },
          ],
        },
        {
          group: "Webhooks",
          endpoints: [
            { method: "POST",   path: "/webhooks", description: "Subscribe to an event (secret shown once)" },
            { method: "GET",    path: "/webhooks", description: "List all subscriptions" },
            { method: "GET",    path: "/webhooks/{id}", description: "Get subscription + last 10 delivery events" },
            { method: "PATCH",  path: "/webhooks/{id}", description: "Update URL or active status" },
            { method: "DELETE", path: "/webhooks/{id}", description: "Remove a subscription" },
            { method: "POST",   path: "/webhooks/{id}/test", description: "Send a test ping to your endpoint" },
          ],
        },
        {
          group: "Analytics",
          endpoints: [
            { method: "GET", path: "/analytics/summary", description: "24h summary: calls, cache rate, response time" },
            { method: "GET", path: "/analytics/usage", description: "Detailed metrics (last_24h · last_7d · last_30d)" },
            { method: "GET", path: "/analytics/reports", description: "Download 30-day CSV report" },
          ],
        },
      ].map(({ group, endpoints }) => (
        <div key={group} className="mb-xl">
          <h3 className="text-headline-sm font-semibold mb-sm">{group}</h3>
          <div className="border border-outline rounded-lg px-md py-xs">
            {endpoints.map((ep) => (
              <Endpoint key={ep.method + ep.path} {...ep} />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

function WebhooksSection() {
  return (
    <div>
      <p className="text-body-md text-on-surface-variant mb-lg">
        Webhooks let OmniAPI push events to your server the moment something happens —
        no polling required.
      </p>

      <Step n={1} title="Create a subscription" />
      <CodeBlock language="bash" code={`curl -X POST https://omniapi-api.onrender.com/api/v1/webhooks \\
  -H "Authorization: Bearer <your_jwt>" \\
  -H "Content-Type: application/json" \\
  -d '{
    "url": "https://yourapp.com/hooks/omniapi",
    "event_type": "orchestrate.complete"
  }'`} />
      <CodeBlock language="json" code={`{
  "webhook_id": 7,
  "url": "https://yourapp.com/hooks/omniapi",
  "event_type": "orchestrate.complete",
  "is_active": true,
  "secret": "a3f9bc8d...",
  "retry_count": 0
}`} />
      <Callout type="warning">
        <code className="font-mono">secret</code> is shown <strong>once only</strong>. Store
        it immediately — use it to verify the <code className="font-mono">X-OmniAPI-Signature</code>{" "}
        header on every incoming payload.
      </Callout>

      <Step n={2} title="Supported event types" />
      <div className="border border-outline rounded-lg px-md py-xs mb-lg">
        {[
          { event: "orchestrate.complete", desc: "All services in a request returned success" },
          { event: "orchestrate.failed",   desc: "One or more services in a request failed" },
          { event: "api_key.created",      desc: "A new OmniAPI key was generated in your account" },
        ].map(({ event, desc }) => (
          <div key={event} className="flex flex-col sm:flex-row sm:items-center gap-sm py-sm border-b border-outline-variant last:border-0">
            <code className="font-mono text-sm text-secondary-fixed shrink-0">{event}</code>
            <span className="text-body-sm text-on-surface-variant">{desc}</span>
          </div>
        ))}
      </div>

      <Step n={3} title="Payload your endpoint receives" />
      <CodeBlock language="json" code={`{
  "event_id": "uuid-string",
  "event_type": "orchestrate.complete",
  "tenant_id": "42",
  "timestamp": "2026-06-03T10:10:05Z",
  "data": {
    "request_id": "a1b2c3d4-...",
    "services": ["weather", "stock"],
    "total_time_ms": 312,
    "results_summary": [
      { "service": "weather", "success": true,  "cache_hit": false },
      { "service": "stock",   "success": true,  "cache_hit": true  }
    ]
  }
}`} />

      <Step n={4} title="Test your endpoint" />
      <CodeBlock language="bash" code={`curl -X POST https://omniapi-api.onrender.com/api/v1/webhooks/7/test \\
  -H "Authorization: Bearer <your_jwt>"`} />
      <Callout type="info">
        OmniAPI retries failed deliveries automatically with exponential back-off. Check
        delivery history at <code className="font-mono">GET /webhooks/{"{id}"}</code> — it
        returns the last 10 delivery attempts with HTTP status codes and timestamps.
      </Callout>
    </div>
  );
}

function CodeExamples() {
  return (
    <div>
      <p className="text-body-md text-on-surface-variant mb-lg">
        Copy-paste examples for common tasks in JavaScript/TypeScript and Python.
      </p>

      <h3 className="text-headline-sm font-semibold mb-sm">JavaScript — call a single service</h3>
      <CodeBlock language="javascript" code={`const response = await fetch(
  "https://omniapi-api.onrender.com/api/v1/orchestrate",
  {
    method: "POST",
    headers: {
      "X-API-Key": process.env.OMNI_API_KEY,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      services: ["stock"],          // only call stock — others are ignored
      params: {
        stock: { symbol: "AAPL" },
      },
    }),
  }
);

const data = await response.json();
console.log(data.results[0].data); // stock data for AAPL`} />

      <h3 className="text-headline-sm font-semibold mt-xl mb-sm">JavaScript — call all three services at once</h3>
      <CodeBlock language="javascript" code={`const response = await fetch(
  "https://omniapi-api.onrender.com/api/v1/orchestrate",
  {
    method: "POST",
    headers: {
      "X-API-Key": process.env.OMNI_API_KEY,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      services: ["weather", "news", "stock"],
      params: {
        weather: { city: "Tokyo" },
        news:    { q: "markets", pageSize: 5 },
        stock:   { symbol: "TSLA" },
      },
    }),
  }
);

const { results } = await response.json();
const weatherData = results.find((r) => r.service === "weather")?.data;
const stockData   = results.find((r) => r.service === "stock")?.data;`} />

      <h3 className="text-headline-sm font-semibold mt-xl mb-sm">Python — call a single service</h3>
      <CodeBlock language="python" code={`import os, requests

response = requests.post(
    "https://omniapi-api.onrender.com/api/v1/orchestrate",
    headers={
        "X-API-Key": os.environ["OMNI_API_KEY"],
        "Content-Type": "application/json",
    },
    json={
        "services": ["news"],          # only news — weather and stock are ignored
        "params": {
            "news": {"q": "climate change", "pageSize": 5},
        },
    },
)

data = response.json()
articles = data["results"][0]["data"]["articles"]`} />

      <h3 className="text-headline-sm font-semibold mt-xl mb-sm">Handling a failed service gracefully</h3>
      <p className="text-body-sm text-on-surface-variant mb-sm">
        If one service fails, the rest still return normally.{" "}
        <code className="font-mono">success: false</code> means that service had an error —
        always check before using the data.
      </p>
      <CodeBlock language="javascript" code={`const { results } = await response.json();

for (const result of results) {
  if (!result.success) {
    console.error(\`\${result.service} failed: \${result.error}\`);
    continue;
  }
  // safe to use result.data
  console.log(\`\${result.service} ok (cache_hit=\${result.cache_hit})\`);
}`} />

      <h3 className="text-headline-sm font-semibold mt-xl mb-sm">Zero-downtime API key rotation</h3>
      <CodeBlock language="bash" code={`# 1. Create new key
curl -X POST https://omniapi-api.onrender.com/api/v1/api-keys \\
  -H "Authorization: Bearer <jwt>" \\
  -H "Content-Type: application/json" \\
  -d '{"name":"Production v2"}'
# → copy the raw_key from the response

# 2. Update your app environment variable to the new key, deploy

# 3. Delete the old key (replace 3 with the old key_id)
curl -X DELETE https://omniapi-api.onrender.com/api/v1/api-keys/3 \\
  -H "Authorization: Bearer <jwt>"`} />
    </div>
  );
}

/* ─── section registry ───────────────────────────────────────────────── */
const SECTION_COMPONENTS: Record<string, React.FC> = {
  "getting-started":  GettingStarted,
  "authentication":   Authentication,
  "external-services": ExternalServices,
  "orchestrate":      OrchestrateSection,
  "api-reference":    ApiReference,
  "webhooks":         WebhooksSection,
  "code-examples":    CodeExamples,
};

/* ─── page ───────────────────────────────────────────────────────────── */
export default function DocsPage() {
  const [active, setActive] = useState<string>(DOCS_SECTIONS[0].id);
  const SectionContent = SECTION_COMPONENTS[active] ?? GettingStarted;

  return (
    <div className="flex flex-col lg:flex-row gap-gutter">
      {/* sidebar */}
      <aside className="lg:w-56 shrink-0">
        <PageHeader
          title="Documentation"
          description="Guides and API reference"
          className="lg:hidden"
        />
        <nav
          className="sticky top-4 bg-white dark:bg-surface border border-outline rounded-xl p-md"
          aria-label="Documentation sections"
        >
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

      {/* content */}
      <article className="flex-1 min-w-0">
        <div className="hidden lg:block mb-xl">
          <PageHeader title="Documentation" description="Guides and API reference" />
        </div>
        <div className="bg-white dark:bg-surface border border-outline rounded-xl p-lg md:p-xl">
          <SectionContent />
        </div>
      </article>
    </div>
  );
}
