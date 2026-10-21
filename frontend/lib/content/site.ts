// Product copy for the public surface of OmniAPI.
//
// Nothing here is invented: every claim describes behaviour that exists in
// `backend/` (parallel fan-out, Redis cache, Celery refresh, rate-limit headers,
// webhook retries, JWT plus X-API-Key auth). Numbers are never invented either.

export const site = {
  name: "OmniAPI",
  tagline: "One call for every third-party API",
  url: "https://omniapi3021.vercel.app",
  apiUrl: "https://omniapi-api.onrender.com/api/v1",
  description:
    "OmniAPI turns any number of third-party APIs into a single call: parallel fan-out, caching, retries and one signed response.",
  docsUrl: "https://omniapi-api.onrender.com/docs",
} as const;

export const hero = {
  kicker: "API orchestration",
  title: "One call fans out. Many answers gather back.",
  body:
    "Register your provider keys once, mint one OmniAPI key, and POST a list of services to a single endpoint. OmniAPI calls them in parallel, caches the results and returns one envelope.",
  primaryCta: { label: "Create a free key", href: "/signup" },
  secondaryCta: { label: "Read the docs", href: "/docs" },
  note: "The diagram is a simulation. Your own requests use the same shape.",
} as const;

/** The fan shown on the landing page. Simulated latencies, stated as such. */
export const demoFan = [
  { name: "weather", latencyMs: 240 },
  { name: "news", latencyMs: 410 },
  { name: "stock", latencyMs: 180 },
] as const;

export const pillars = [
  {
    index: "01",
    title: "Fan out in parallel",
    body:
      "Name every service you need in the services array. OmniAPI calls them at the same time instead of one after another, so total latency is the slowest provider, not the sum of all of them.",
  },
  {
    index: "02",
    title: "Cache the boring answers",
    body:
      "Each result reports cache_hit. A hit is served from Redis in under a millisecond and costs no provider quota. A miss is fetched by a Celery worker and cached for the next caller.",
  },
  {
    index: "03",
    title: "Return one envelope",
    body:
      "Every response carries the same shape: request_id, total_time_ms and a results array with one entry per service, so your code reads one response instead of three.",
  },
] as const;

export const capabilities = [
  {
    title: "API keys",
    body:
      "One key per application. Permissions per key, an optional expiry date, and the raw key shown exactly once when it is created.",
    href: "/api-keys",
    cta: "Manage keys",
  },
  {
    title: "External services",
    body:
      "Store a provider key for each third-party API. It is encrypted at rest with AES-256 and never appears in any response.",
    href: "/external-services",
    cta: "Connect a service",
  },
  {
    title: "Orchestrate",
    body:
      "A playground that builds the request, runs it against the live gateway and shows the real response times next to the code.",
    href: "/orchestrate",
    cta: "Open the playground",
  },
  {
    title: "Webhooks",
    body:
      "Subscribe to orchestrate.complete, orchestrate.failed and api_key.created. Failed deliveries retry with exponential backoff.",
    href: "/webhooks",
    cta: "Add a webhook",
  },
] as const;

export const steps = [
  {
    title: "Register your provider keys",
    body:
      "Add each third-party API under External Services. OmniAPI encrypts the key and calls the provider on your behalf.",
  },
  {
    title: "Mint one OmniAPI key",
    body:
      "Create a key for your application. It carries the permissions you choose and an expiry date if you want one.",
  },
  {
    title: "Name the services you need",
    body:
      "POST a services array with the params for each one. Leave out what you do not need and it is never called.",
  },
  {
    title: "Read one envelope",
    body:
      "The response holds a results entry per service, each with success, cache_hit and response_time_ms.",
  },
] as const;

export const requestExample = `curl -X POST ${site.apiUrl}/orchestrate \\
  -H "X-API-Key: omni_xK9mP2qL..." \\
  -H "Content-Type: application/json" \\
  -d '{
    "services": ["weather", "news", "stock"],
    "params": {
      "weather": { "city": "Lisbon" },
      "news":    { "q": "markets", "pageSize": 5 },
      "stock":   { "symbol": "NVDA" }
    }
  }'`;

export const responseExample = `{
  "request_id": "a1b2c3d4-e5f6-...",
  "total_time_ms": 245,
  "results": [
    { "service": "weather", "success": true, "cache_hit": true,  "response_time_ms": 0 },
    { "service": "news",    "success": true, "cache_hit": false, "response_time_ms": 241 },
    { "service": "stock",   "success": true, "cache_hit": true,  "response_time_ms": 0 }
  ]
}`;

export const footerNote = {
  builtWith: "Next.js, Tailwind, GSAP and Lenis",
  liveApi: site.apiUrl,
  apiDocs: site.docsUrl,
} as const;
