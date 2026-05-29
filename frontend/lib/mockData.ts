import type {
  ActivityLog,
  AnalyticsSummary,
  ApiKey,
  ExternalService,
  UsageDataPoint,
  User,
  Webhook,
} from "@/types";

export const MOCK_USER: User = {
  id: "user_1",
  name: "Alex Morgan",
  email: "alex@example.com",
  company: "Acme Corp",
};

export const MOCK_API_KEYS: ApiKey[] = [
  {
    id: "key_1",
    name: "Production Billing",
    keyPrefix: "omni_live",
    key: "omni_live_sk_8f3a2b1c9d4e5f6a7b8c9d0e",
    permissions: ["read", "write"],
    createdAt: "2025-04-01T10:00:00Z",
    expiresAt: "2026-04-01T10:00:00Z",
    lastUsed: "2025-05-28T14:30:00Z",
    status: "active",
  },
  {
    id: "key_2",
    name: "Staging Tests",
    keyPrefix: "omni_test",
    key: "omni_test_sk_a1b2c3d4e5f6a7b8c9d0e1f2",
    permissions: ["read"],
    createdAt: "2025-03-15T08:00:00Z",
    expiresAt: null,
    lastUsed: "2025-05-27T09:15:00Z",
    status: "active",
  },
  {
    id: "key_3",
    name: "Legacy Integration",
    keyPrefix: "omni_live",
    key: "omni_live_sk_legacy00000000001",
    permissions: ["read", "write", "admin"],
    createdAt: "2024-11-20T12:00:00Z",
    expiresAt: "2025-06-01T00:00:00Z",
    lastUsed: "2025-05-20T16:45:00Z",
    status: "expiring",
  },
];

export const MOCK_SERVICES: ExternalService[] = [
  {
    id: "svc_1",
    name: "Stripe Payments",
    serviceType: "stripe",
    status: "connected",
    rateLimit: 5000,
    createdAt: "2025-02-10T10:00:00Z",
    lastSync: "2025-05-28T12:00:00Z",
  },
  {
    id: "svc_2",
    name: "Twilio SMS",
    serviceType: "twilio",
    status: "connected",
    rateLimit: 1000,
    createdAt: "2025-03-01T14:00:00Z",
    lastSync: "2025-05-28T11:30:00Z",
  },
  {
    id: "svc_3",
    name: "SendGrid Email",
    serviceType: "sendgrid",
    status: "error",
    rateLimit: null,
    createdAt: "2025-01-15T09:00:00Z",
    lastSync: "2025-05-25T08:00:00Z",
  },
];

export const MOCK_WEBHOOKS: Webhook[] = [
  {
    id: "wh_1",
    name: "Payment Events",
    url: "https://api.acme.com/webhooks/payments",
    events: ["payment.succeeded", "payment.failed"],
    status: "active",
    createdAt: "2025-03-10T10:00:00Z",
    lastTriggered: "2025-05-28T13:00:00Z",
    successRate: 99.2,
  },
  {
    id: "wh_2",
    name: "User Signups",
    url: "https://api.acme.com/webhooks/users",
    events: ["user.created"],
    status: "active",
    createdAt: "2025-04-05T14:00:00Z",
    lastTriggered: "2025-05-28T10:30:00Z",
    successRate: 100,
  },
];

export const MOCK_ACTIVITY: ActivityLog[] = [
  {
    id: "act_1",
    status: 200,
    statusLabel: "200 OK",
    method: "GET",
    endpoint: "/api/v1/users/profile",
    latency: 32,
    timestamp: new Date(Date.now() - 60000).toISOString(),
  },
  {
    id: "act_2",
    status: 201,
    statusLabel: "201 CREATED",
    method: "POST",
    endpoint: "/api/v1/transactions",
    latency: 145,
    timestamp: new Date(Date.now() - 120000).toISOString(),
  },
  {
    id: "act_3",
    status: 401,
    statusLabel: "401 UNAUTH",
    method: "GET",
    endpoint: "/api/v1/admin/settings",
    latency: 12,
    timestamp: new Date(Date.now() - 300000).toISOString(),
  },
  {
    id: "act_4",
    status: 200,
    statusLabel: "200 OK",
    method: "GET",
    endpoint: "/api/v1/products?limit=50",
    latency: 88,
    timestamp: new Date(Date.now() - 720000).toISOString(),
  },
];

export const MOCK_ANALYTICS_SUMMARY: AnalyticsSummary = {
  callsToday: 1200000,
  callsChange: 12,
  cacheHitPercent: 84.5,
  avgResponseMs: 42,
  responseChangeMs: 3,
};

export const MOCK_USAGE_DATA: UsageDataPoint[] = [
  { time: "00:00", requests: 1200 },
  { time: "04:00", requests: 800 },
  { time: "06:00", requests: 2100 },
  { time: "08:00", requests: 3500 },
  { time: "10:00", requests: 4200 },
  { time: "12:00", requests: 3800 },
  { time: "14:00", requests: 4500 },
  { time: "16:00", requests: 3900 },
  { time: "18:00", requests: 3200 },
  { time: "20:00", requests: 2800 },
  { time: "22:00", requests: 1900 },
  { time: "24:00", requests: 1500 },
];

export const MOCK_CACHE_DATA = [
  { name: "Hit", value: 84.5 },
  { name: "Miss", value: 15.5 },
];

export const MOCK_LATENCY_DATA = [
  { time: "Mon", p50: 38, p95: 120 },
  { time: "Tue", p50: 42, p95: 135 },
  { time: "Wed", p50: 40, p95: 128 },
  { time: "Thu", p50: 45, p95: 142 },
  { time: "Fri", p50: 41, p95: 130 },
  { time: "Sat", p50: 35, p95: 110 },
  { time: "Sun", p50: 33, p95: 105 },
];

export const MOCK_ENDPOINT_DATA = [
  { endpoint: "/users", calls: 45000 },
  { endpoint: "/transactions", calls: 32000 },
  { endpoint: "/products", calls: 28000 },
  { endpoint: "/webhooks", calls: 12000 },
];
