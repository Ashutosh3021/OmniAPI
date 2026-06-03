export interface Webhook {
  webhook_id: number;
  url: string;
  event_type: string;
  is_active: boolean;
  retry_count: number;
  created_at: string;
}
