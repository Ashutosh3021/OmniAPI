export interface AnalyticsSummary {
  calls_today: number;
  calls_change: number;
  cache_hit_percent: number;
  avg_response_ms: number;
  response_change_ms: number;
}

export interface UsageMetrics {
  total_calls: number;
  successful_calls: number;
  failed_calls: number;
  cache_hits: number;
  cache_hit_rate: number;
  avg_response_time_ms: number;
  estimated_cost_saved: number;
}

export interface ServiceBreakdown {
  service_name: string;
  call_count: number;
  cache_hits: number;
  avg_response_time_ms: number;
  error_count: number;
}

export interface AnalyticsResponse {
  period: string;
  metrics: UsageMetrics;
  by_service: ServiceBreakdown[];
  generated_at: string;
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
