export interface AnalyticsSummary {
  callsToday: number;
  callsChange: number;
  cacheHitPercent: number;
  avgResponseMs: number;
  responseChangeMs: number;
}

export interface UsageDataPoint {
  time: string;
  requests: number;
}

export interface ActivityLog {
  id: string;
  status: number;
  statusLabel: string;
  method: string;
  endpoint: string;
  latency: number;
  timestamp: string;
}
