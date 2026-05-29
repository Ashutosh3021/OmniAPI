export interface ApiKey {
  id: string;
  name: string;
  keyPrefix: string;
  key: string;
  permissions: string[];
  createdAt: string;
  expiresAt: string | null;
  lastUsed: string | null;
  status: "active" | "expiring" | "revoked";
}

export interface ExternalService {
  id: string;
  name: string;
  serviceType: string;
  status: "connected" | "error" | "disconnected";
  rateLimit: number | null;
  createdAt: string;
  lastSync: string;
}
