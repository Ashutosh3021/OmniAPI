export interface Webhook {
  id: string;
  name: string;
  url: string;
  events: string[];
  status: "active" | "paused" | "failed";
  createdAt: string;
  lastTriggered: string | null;
  successRate: number;
}
