import type { FC, ReactNode } from "react";
import { Badge } from "@/components/shared/Badge";
import { CodePanel } from "@/components/shared/CodePanel";
import { site } from "./site";

/* ── helpers ──────────────────────────────────────────────────────────── */

function Callout({
  type = "info",
  children,
}: {
  type?: "info" | "warning" | "tip";
  children: ReactNode;
}) {
  const styles = {
    info: "border-accent/30 bg-accent/8",
    warning: "border-warn/40 bg-warn/10",
    tip: "border-ok/30 bg-ok/8",
  };
  const labels = { info: "Note", warning: "Important", tip: "Tip" };

  return (
    <div className={cn2("mb-8 rounded border p-4 text-ui", styles[type])}>
      <span className="label-wire mb-1.5 block">{labels[type]}</span>
      <div className="text-ink">{children}</div>
    </div>
  );
}

function cn2(...parts: (string | false | undefined)[]) {
  return parts.filter(Boolean).join(" ");
}

function Step({ n, title }: { n: number; title: string }) {
  return (
    <div className="mt-10 mb-4 flex items-center gap-3">
      <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded bg-ink font-mono text-micro font-semibold text-ground">
        {n}
      </span>
      <h3 className="t-subhead text-ink">{title}</h3>
    </div>
  );
}

const methodTone: Record<string, string> = {
  GET: "text-ok border-ok/35 bg-ok/8",
  POST: "text-accent border-accent/35 bg-accent/8",
  PATCH: "text-warn border-warn/35 bg-warn/8",
  PUT: "text-warn border-warn/35 bg-warn/8",
  DELETE: "text-bad border-bad/35 bg-bad/8",
};

function Endpoint({
  method,
  path,
  description,
}: {
  method: string;
  path: string;
  description: string;
}) {
  return (
    <div className="flex flex-col gap-1.5 border-b border-ink/12 py-2.5 last:border-0 sm:flex-row sm:items-center sm:gap-3">
      <span
        className={cn2(
          "inline-block w-16 shrink-0 rounded border px-1.5 py-0.5 text-center font-mono text-micro font-semibold uppercase",
          methodTone[method] ?? "border-ink/20 text-muted"
        )}
      >
        {method}
      </span>
      <code className="shrink-0 font-mono text-[0.8125rem] text-accent">
        {path}
      </code>
      <span className="text-ui text-muted">{description}</span>
    </div>
  );
}

function Para({ children }: { children: ReactNode }) {
  return (
    <p className="mb-6 max-w-[68ch] text-ui leading-relaxed text-muted">
      {children}
    </p>
  );
}

function H3({ children }: { children: ReactNode }) {
  return <h3 className="t-subhead mb-3 mt-8 text-ink">{children}</h3>;
}

/* ── sections ─────────────────────────────────────────────────────────── */

export function GettingStarted() {
  return (
    <div>
      <Para>
        OmniAPI is a unified gateway that lets your application call several
        external APIs through a <strong className="text-ink">single endpoint</strong>{" "}
        using a single key. It handles caching, rate limiting, parallel fetching
        and retries for you automatically.
      </Para>

      <H3>How it works in four steps</H3>
      <ol className="mb-8 list-none space-y-3">
        {[
          "Create an OmniAPI account and sign in.",
          "Go to External services and add the API key for each provider, for example OpenWeatherMap or NewsAPI.",
          "Go to API keys and generate one OmniAPI key for your application.",
          "Call POST /api/v1/orchestrate with the services you want. OmniAPI calls them in parallel and returns one envelope.",
        ].map((step, i) => (
          <li key={i} className="flex gap-3">
            <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full border border-ink/25 font-mono text-micro font-semibold text-ink">
              {i + 1}
            </span>
            <span className="text-ui text-muted">{step}</span>
          </li>
        ))}
      </ol>

      <Callout type="tip">
        The live API is at <code className="font-mono text-[0.8125rem]">{site.apiUrl}</code>.
        Interactive API docs are available at{" "}
        <a
          href={site.docsUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="link"
        >
          {site.docsUrl.replace("https://", "")}
        </a>
        .
      </Callout>

      <H3>Health check</H3>
      <CodePanel
        language="bash"
        code={`curl ${site.apiUrl}/health`}
      />
    </div>
  );
}

export function Authentication() {
  return (
    <div>
      <Para>
        OmniAPI uses two kinds of credential, depending on who is making the
        request.
      </Para>

      <H3>1. JWT bearer token, for the dashboard and trusted servers</H3>
      <Para>
        When you sign in through the dashboard or the{" "}
        <code className="font-mono text-[0.8125rem]">/auth/login</code> endpoint,
        you receive an <strong className="text-ink">access token</strong> and a{" "}
        <strong className="text-ink">refresh token</strong>. Pass the access
        token in the <code className="font-mono text-[0.8125rem]">Authorization</code>{" "}
        header.
      </Para>
      <CodePanel
        language="bash"
        code={`# 1. Sign in
curl -X POST ${site.apiUrl}/auth/login \\
  -H "Content-Type: application/json" \\
  -d '{"email":"you@example.com","password":"yourpassword"}'

# Response
# { "access_token": "eyJ...", "refresh_token": "eyJ..." }

# 2. Use the token
curl ${site.apiUrl}/api-keys \\
  -H "Authorization: Bearer eyJ..."`}
      />

      <Callout type="info">
        Access tokens expire. When one does, call{" "}
        <code className="font-mono text-[0.8125rem]">POST /auth/refresh</code>{" "}
        with your <code className="font-mono text-[0.8125rem]">refresh_token</code>{" "}
        to get a new pair. The dashboard does this for you.
      </Callout>

      <H3>2. OmniAPI key, for your application</H3>
      <Para>
        For your application code, generate an OmniAPI key from the API keys
        page. Pass it in the{" "}
        <code className="font-mono text-[0.8125rem]">X-API-Key</code> header.
      </Para>
      <CodePanel
        language="bash"
        code={`curl -X POST ${site.apiUrl}/orchestrate \\
  -H "X-API-Key: omni_xK9mP2qL..." \\
  -H "Content-Type: application/json" \\
  -d '{"services":["weather"],"params":{"weather":{"city":"London"}}}'`}
      />

      <Callout type="warning">
        Your OmniAPI key is shown <strong className="text-ink">only once</strong>{" "}
        when it is created. Store it in an environment variable right away. If
        you lose it, delete it and generate a new one.
      </Callout>
    </div>
  );
}

export function ExternalServices() {
  return (
    <div>
      <Para>
        Before you can orchestrate a service, register the API key for that
        provider under <strong className="text-ink">External services</strong>.
        OmniAPI stores it encrypted and uses it on your behalf, so your provider
        key never appears in a response.
      </Para>

      <H3>Supported services</H3>
      <div className="mb-8 overflow-x-auto">
        <table className="data-table">
          <thead>
            <tr>
              <th scope="col">service_name</th>
              <th scope="col">Provider</th>
              <th scope="col">Where to get a key</th>
            </tr>
          </thead>
          <tbody>
            {[
              ["weather", "OpenWeatherMap", "openweathermap.org/api"],
              ["news", "NewsAPI", "newsapi.org"],
              ["stock", "Your stock data provider", "your provider's dashboard"],
            ].map(([name, provider, link]) => (
              <tr key={name}>
                <td>
                  <code className="font-mono text-accent">{name}</code>
                </td>
                <td className="text-muted">{provider}</td>
                <td className="font-mono text-micro text-muted">{link}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <Step n={1} title="Add a service" />
      <CodePanel
        language="bash"
        code={`curl -X POST ${site.apiUrl}/external-services \\
  -H "Authorization: Bearer <your_jwt>" \\
  -H "Content-Type: application/json" \\
  -d '{
    "service_name": "weather",
    "api_key": "your_openweathermap_api_key",
    "max_calls_per_hour": 100
  }'`}
      />

      <Step n={2} title="List your services" />
      <CodePanel
        language="bash"
        code={`curl ${site.apiUrl}/external-services \\
  -H "Authorization: Bearer <your_jwt>"`}
      />
      <CodePanel
        language="json"
        code={`[
  { "service_id": 1, "service_name": "weather", "max_calls_per_hour": 100, "status": "active" },
  { "service_id": 2, "service_name": "news",    "max_calls_per_hour": 60,  "status": "active" },
  { "service_id": 3, "service_name": "stock",   "max_calls_per_hour": 50,  "status": "active" }
]`}
      />

      <Step n={3} title="Update or remove a service" />
      <CodePanel
        language="bash"
        code={`# Pause a service without deleting the key
curl -X PATCH ${site.apiUrl}/external-services/1 \\
  -H "Authorization: Bearer <your_jwt>" \\
  -H "Content-Type: application/json" \\
  -d '{"status":"inactive"}'

# Remove it permanently
curl -X DELETE ${site.apiUrl}/external-services/1 \\
  -H "Authorization: Bearer <your_jwt>"`}
      />
    </div>
  );
}

export function OrchestrateSection() {
  return (
    <div>
      <Para>
        The <code className="font-mono text-[0.8125rem]">/orchestrate</code>{" "}
        endpoint is the core of OmniAPI. You send one request naming the
        services you want. OmniAPI calls them in parallel, caches the results
        and returns them together.
      </Para>

      <H3>Calling one specific service</H3>
      <Para>
        Say you have three external services configured:{" "}
        <Badge tone="accent">weather</Badge> <Badge tone="accent">news</Badge>{" "}
        <Badge tone="accent">stock</Badge>. Right now you only want stock data.
        Put just <code className="font-mono text-[0.8125rem]">&quot;stock&quot;</code>{" "}
        in the <code className="font-mono text-[0.8125rem]">services</code> array
        and OmniAPI will ignore the other two entirely.
      </Para>
      <CodePanel
        language="bash"
        code={`# Only call the "stock" service
curl -X POST ${site.apiUrl}/orchestrate \\
  -H "X-API-Key: omni_xK9mP2qL..." \\
  -H "Content-Type: application/json" \\
  -d '{
    "services": ["stock"],
    "params": {
      "stock": { "symbol": "AAPL" }
    }
  }'`}
      />
      <Callout type="tip">
        The <code className="font-mono text-[0.8125rem]">services</code> array
        controls which services are called for <em>this request</em>. Other
        services in your account do not affect the call.
      </Callout>

      <H3>Example: three services, one of them called</H3>
      <Para>
        Your account has these three external services registered:
      </Para>
      <div className="mb-6 grid grid-cols-1 gap-3 sm:grid-cols-3">
        {[
          { label: "Service A", name: "weather" },
          { label: "Service B", name: "news" },
          { label: "Service C", name: "stock" },
        ].map(({ label, name }) => (
          <div key={name} className="rounded border border-ink/15 p-3">
            <p className="label-wire">{label}</p>
            <code className="font-mono text-[0.8125rem] text-accent">{name}</code>
          </div>
        ))}
      </div>
      <Para>
        To call only Service C, which is stock, send exactly this:
      </Para>
      <CodePanel
        language="bash"
        code={`curl -X POST ${site.apiUrl}/orchestrate \\
  -H "X-API-Key: omni_xK9mP2qL..." \\
  -H "Content-Type: application/json" \\
  -d '{
    "services": ["stock"],
    "params": {
      "stock": { "symbol": "TSLA" }
    }
  }'`}
      />
      <CodePanel
        language="json"
        code={`{
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
}`}
      />

      <H3>Calling several services at once</H3>
      <Para>
        Add more names to <code className="font-mono text-[0.8125rem]">services</code>.
        OmniAPI calls them all in parallel and returns one entry per service in
        the results array.
      </Para>
      <CodePanel
        language="bash"
        code={`curl -X POST ${site.apiUrl}/orchestrate \\
  -H "X-API-Key: omni_xK9mP2qL..." \\
  -H "Content-Type: application/json" \\
  -d '{
    "services": ["weather", "news", "stock"],
    "params": {
      "weather": { "city": "New York" },
      "news":    { "q": "AI", "pageSize": 3 },
      "stock":   { "symbol": "NVDA" }
    }
  }'`}
      />

      <H3>Reading cache_hit</H3>
      <Para>
        Every result carries a{" "}
        <code className="font-mono text-[0.8125rem]">cache_hit</code> field.
      </Para>
      <div className="mb-8 space-y-2">
        <div className="flex flex-col gap-2 rounded border border-ink/12 p-3 sm:flex-row sm:items-start sm:gap-3">
          <Badge tone="ok">true</Badge>
          <span className="text-ui text-muted">
            The answer came from Redis.{" "}
            <code className="font-mono text-[0.8125rem]">response_time_ms</code> is{" "}
            <code className="font-mono text-[0.8125rem]">0</code> and no call was
            made to the provider, so you keep your quota.
          </span>
        </div>
        <div className="flex flex-col gap-2 rounded border border-ink/12 p-3 sm:flex-row sm:items-start sm:gap-3">
          <Badge tone="bad">false</Badge>
          <span className="text-ui text-muted">
            The answer was fetched from the provider by a background Celery task
            and then cached for the next caller.
          </span>
        </div>
      </div>

      <H3>Rate limit headers</H3>
      <Para>
        Every orchestrate response carries these headers, so your application
        can back off before it hits the limit.
      </Para>
      <CodePanel
        language="http"
        code={`X-RateLimit-Limit: 100
X-RateLimit-Remaining: 73`}
      />
    </div>
  );
}

export function ApiReference() {
  const groups = [
    {
      group: "Auth",
      endpoints: [
        { method: "POST", path: "/auth/register", description: "Create an account" },
        { method: "POST", path: "/auth/login", description: "Get an access and refresh token pair" },
        { method: "POST", path: "/auth/refresh", description: "Rotate tokens with a refresh token" },
        { method: "GET", path: "/auth/me", description: "Return the current user" },
      ],
    },
    {
      group: "API keys",
      endpoints: [
        { method: "POST", path: "/api-keys", description: "Create a key, the raw key is shown once" },
        { method: "GET", path: "/api-keys", description: "List your keys" },
        { method: "GET", path: "/api-keys/{key_id}", description: "Get one key" },
        { method: "PATCH", path: "/api-keys/{key_id}", description: "Update the name or expiry date" },
        { method: "DELETE", path: "/api-keys/{key_id}", description: "Delete a key" },
      ],
    },
    {
      group: "External services",
      endpoints: [
        { method: "POST", path: "/external-services", description: "Register a provider API key" },
        { method: "GET", path: "/external-services", description: "List your services" },
        { method: "GET", path: "/external-services/{id}", description: "Get one service" },
        { method: "PATCH", path: "/external-services/{id}", description: "Update the key, rate limit or status" },
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
        { method: "POST", path: "/webhooks", description: "Subscribe to an event, the secret is shown once" },
        { method: "GET", path: "/webhooks", description: "List your subscriptions" },
        { method: "GET", path: "/webhooks/{id}", description: "Get a subscription and its last ten deliveries" },
        { method: "PATCH", path: "/webhooks/{id}", description: "Update the URL or the active status" },
        { method: "DELETE", path: "/webhooks/{id}", description: "Remove a subscription" },
        { method: "POST", path: "/webhooks/{id}/test", description: "Send a test ping to your endpoint" },
      ],
    },
    {
      group: "Analytics",
      endpoints: [
        { method: "GET", path: "/analytics/summary", description: "24 hour summary: calls, cache rate, response time" },
        { method: "GET", path: "/analytics/usage", description: "Detailed metrics over 24 hours, 7 days or 30 days" },
        { method: "GET", path: "/analytics/reports", description: "Download the 30 day CSV report" },
      ],
    },
  ];

  return (
    <div>
      <Para>
        Every endpoint lives under{" "}
        <code className="font-mono text-[0.8125rem]">{site.apiUrl}</code>.
        Interactive Swagger docs are at{" "}
        <a
          href={site.docsUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="link"
        >
          {site.docsUrl.replace("https://", "")}
        </a>
        .
      </Para>

      {groups.map(({ group, endpoints }) => (
        <div key={group} className="mb-8">
          <H3>{group}</H3>
          <div className="rounded border border-ink/12 px-4">
            {endpoints.map((ep) => (
              <Endpoint key={ep.method + ep.path} {...ep} />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

export function WebhooksSection() {
  return (
    <div>
      <Para>
        Webhooks let OmniAPI push events to your server the moment something
        happens, so you do not have to poll.
      </Para>

      <Step n={1} title="Create a subscription" />
      <CodePanel
        language="bash"
        code={`curl -X POST ${site.apiUrl}/webhooks \\
  -H "Authorization: Bearer <your_jwt>" \\
  -H "Content-Type: application/json" \\
  -d '{
    "url": "https://yourapp.com/hooks/omniapi",
    "event_type": "orchestrate.complete"
  }'`}
      />
      <CodePanel
        language="json"
        code={`{
  "webhook_id": 7,
  "url": "https://yourapp.com/hooks/omniapi",
  "event_type": "orchestrate.complete",
  "is_active": true,
  "secret": "a3f9bc8d...",
  "retry_count": 0
}`}
      />
      <Callout type="warning">
        The <code className="font-mono text-[0.8125rem]">secret</code> is shown{" "}
        <strong className="text-ink">once only</strong>. Store it straight away
        and use it to verify the{" "}
        <code className="font-mono text-[0.8125rem]">X-OmniAPI-Signature</code>{" "}
        header on every incoming payload.
      </Callout>

      <Step n={2} title="Supported event types" />
      <div className="mb-8 rounded border border-ink/12 px-4">
        {[
          {
            event: "orchestrate.complete",
            desc: "Every service in a request returned success",
          },
          {
            event: "orchestrate.failed",
            desc: "One or more services in a request failed",
          },
          {
            event: "api_key.created",
            desc: "A new OmniAPI key was generated in your account",
          },
        ].map(({ event, desc }) => (
          <div
            key={event}
            className="flex flex-col gap-1 border-b border-ink/12 py-2.5 last:border-0 sm:flex-row sm:items-center sm:gap-3"
          >
            <code className="shrink-0 font-mono text-[0.8125rem] text-accent">
              {event}
            </code>
            <span className="text-ui text-muted">{desc}</span>
          </div>
        ))}
      </div>

      <Step n={3} title="The payload your endpoint receives" />
      <CodePanel
        language="json"
        code={`{
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
}`}
      />

      <Step n={4} title="Test your endpoint" />
      <CodePanel
        language="bash"
        code={`curl -X POST ${site.apiUrl}/webhooks/7/test \\
  -H "Authorization: Bearer <your_jwt>"`}
      />
      <Callout type="info">
        OmniAPI retries failed deliveries automatically with exponential backoff.
        Delivery history is available at{" "}
        <code className="font-mono text-[0.8125rem]">GET /webhooks/{"{id}"}</code>,
        which returns the last ten attempts with their HTTP status codes and
        timestamps.
      </Callout>
    </div>
  );
}

export function CodeExamples() {
  return (
    <div>
      <Para>
        Copy and paste examples for the common cases, in JavaScript and in
        Python.
      </Para>

      <H3>JavaScript: call one service</H3>
      <CodePanel
        language="javascript"
        code={`const response = await fetch(
  "${site.apiUrl}/orchestrate",
  {
    method: "POST",
    headers: {
      "X-API-Key": process.env.OMNI_API_KEY,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      services: ["stock"],
      params: {
        stock: { symbol: "AAPL" },
      },
    }),
  }
);

const data = await response.json();
console.log(data.results[0].data);`}
      />

      <H3>JavaScript: call three services at once</H3>
      <CodePanel
        language="javascript"
        code={`const response = await fetch(
  "${site.apiUrl}/orchestrate",
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
const weather = results.find((r) => r.service === "weather")?.data;
const stock = results.find((r) => r.service === "stock")?.data;`}
      />

      <H3>Python: call one service</H3>
      <CodePanel
        language="python"
        code={`import os, requests

response = requests.post(
    "${site.apiUrl}/orchestrate",
    headers={
        "X-API-Key": os.environ["OMNI_API_KEY"],
        "Content-Type": "application/json",
    },
    json={
        "services": ["news"],
        "params": {
            "news": {"q": "climate change", "pageSize": 5},
        },
    },
)

data = response.json()
articles = data["results"][0]["data"]["articles"]`}
      />

      <H3>Handling a service that fails</H3>
      <Para>
        If one service fails, the rest still come back normally. A{" "}
        <code className="font-mono text-[0.8125rem]">success: false</code> means
        that service had an error, so always check before you use the data.
      </Para>
      <CodePanel
        language="javascript"
        code={`const { results } = await response.json();

for (const result of results) {
  if (!result.success) {
    console.error(\`\${result.service} failed: \${result.error}\`);
    continue;
  }
  console.log(\`\${result.service} ok, cache_hit=\${result.cache_hit}\`);
}`}
      />

      <H3>Rotating a key with no downtime</H3>
      <CodePanel
        language="bash"
        code={`# 1. Create the new key
curl -X POST ${site.apiUrl}/api-keys \\
  -H "Authorization: Bearer <jwt>" \\
  -H "Content-Type: application/json" \\
  -d '{"name":"Production v2"}'
# copy raw_key from the response

# 2. Update your environment variable and deploy

# 3. Delete the old key, replacing 3 with the old key_id
curl -X DELETE ${site.apiUrl}/api-keys/3 \\
  -H "Authorization: Bearer <jwt>"`}
      />
    </div>
  );
}

export const DOCS_CONTENT: Record<string, FC> = {
  "getting-started": GettingStarted,
  authentication: Authentication,
  "external-services": ExternalServices,
  orchestrate: OrchestrateSection,
  "api-reference": ApiReference,
  webhooks: WebhooksSection,
  "code-examples": CodeExamples,
};
