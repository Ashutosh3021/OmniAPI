export interface ApiKey {
  key_id: number;
  name: string;
  is_active: boolean;
  expires_at: string | null;
  created_at: string;
  raw_key?: string; // only present in APIKeyCreatedResponse
}

/** Mirrors the backend ExternalServiceResponse. */
export interface ExternalService {
  service_id: number;
  service_name: string;
  max_calls_per_hour: number;
  status: "active" | "inactive" | "error";
  created_at: string;
}
