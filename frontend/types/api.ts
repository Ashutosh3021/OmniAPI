export interface ApiKey {
  key_id: number;
  name: string;
  is_active: boolean;
  expires_at: string | null;
  created_at: string;
  raw_key?: string; // only present in APIKeyCreatedResponse
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
