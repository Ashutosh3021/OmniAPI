import {
  MOCK_ACTIVITY,
  MOCK_ANALYTICS_SUMMARY,
  MOCK_API_KEYS,
  MOCK_SERVICES,
  MOCK_USER,
  MOCK_WEBHOOKS,
} from "./mockData";
import { generateId } from "./utils";
import type {
  ActivityLog,
  AnalyticsSummary,
  ApiKey,
  ExternalService,
  User,
  Webhook,
} from "@/types";

interface MockStore {
  user: User;
  apiKeys: ApiKey[];
  services: ExternalService[];
  webhooks: Webhook[];
  activity: ActivityLog[];
  analytics: AnalyticsSummary;
}

const globalForStore = globalThis as unknown as {
  __omniMockStore?: MockStore;
};

function createStore(): MockStore {
  return {
    user: { ...MOCK_USER },
    apiKeys: [...MOCK_API_KEYS],
    services: [...MOCK_SERVICES],
    webhooks: [...MOCK_WEBHOOKS],
    activity: [...MOCK_ACTIVITY],
    analytics: { ...MOCK_ANALYTICS_SUMMARY },
  };
}

export function getStore(): MockStore {
  if (!globalForStore.__omniMockStore) {
    globalForStore.__omniMockStore = createStore();
  }
  return globalForStore.__omniMockStore;
}

export function createApiKeyRecord(
  data: Omit<ApiKey, "id" | "key" | "keyPrefix" | "createdAt" | "lastUsed" | "status"> & {
    name: string;
    permissions: string[];
    expiresAt: string | null;
  }
): ApiKey {
  const store = getStore();
  const key = `omni_live_sk_${Math.random().toString(36).slice(2, 18)}`;
  const record: ApiKey = {
    id: generateId("key"),
    name: data.name,
    keyPrefix: "omni_live",
    key,
    permissions: data.permissions,
    createdAt: new Date().toISOString(),
    expiresAt: data.expiresAt,
    lastUsed: null,
    status: "active",
  };
  store.apiKeys.unshift(record);
  return record;
}

export function createServiceRecord(
  data: Omit<ExternalService, "id" | "status" | "createdAt" | "lastSync">
): ExternalService {
  const store = getStore();
  const record: ExternalService = {
    id: generateId("svc"),
    ...data,
    status: "connected",
    createdAt: new Date().toISOString(),
    lastSync: new Date().toISOString(),
  };
  store.services.unshift(record);
  return record;
}

export function createWebhookRecord(
  data: Omit<Webhook, "id" | "status" | "createdAt" | "lastTriggered" | "successRate">
): Webhook {
  const store = getStore();
  const record: Webhook = {
    id: generateId("wh"),
    ...data,
    status: "active",
    createdAt: new Date().toISOString(),
    lastTriggered: null,
    successRate: 100,
  };
  store.webhooks.unshift(record);
  return record;
}
