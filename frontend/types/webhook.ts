export interface WebhookDelivery {
  event_id: number;
  event_type: string;
  status: string;
  http_status_code: number | null;
  attempt_count: number;
  delivered_at: string | null;
  created_at: string;
}

export interface Webhook {
  webhook_id: number;
  url: string;
  event_type: string;
  is_active: boolean;
  retry_count: number;
  created_at: string;
  /** Present on the detail endpoint only. */
  recent_events?: WebhookDelivery[];
}
