export const API_BASE =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export const NAV_ITEMS = [
  { href: "/dashboard", label: "Overview", icon: "LayoutDashboard" },
  { href: "/api-keys", label: "API keys", icon: "Key" },
  { href: "/external-services", label: "Services", icon: "Plug" },
  { href: "/orchestrate", label: "Orchestrate", icon: "GitBranch" },
  { href: "/analytics", label: "Analytics", icon: "BarChart3" },
  { href: "/webhooks", label: "Webhooks", icon: "Webhook" },
  { href: "/settings", label: "Settings", icon: "Settings" },
] as const;

export const SERVICE_TYPES = [
  { value: "weather", label: "OpenWeatherMap" },
  { value: "news", label: "NewsAPI" },
  { value: "stock", label: "Stock data provider" },
] as const;

export const DOCS_SECTIONS = [
  { id: "getting-started", title: "Getting started" },
  { id: "authentication", title: "Authentication" },
  { id: "external-services", title: "External services" },
  { id: "orchestrate", title: "Orchestrating calls" },
  { id: "api-reference", title: "API reference" },
  { id: "webhooks", title: "Webhooks" },
  { id: "code-examples", title: "Code examples" },
] as const;

export const WEBHOOK_EVENT_TYPES = [
  { value: "orchestrate.complete", label: "orchestrate.complete" },
  { value: "orchestrate.failed", label: "orchestrate.failed" },
  { value: "api_key.created", label: "api_key.created" },
] as const;

export const TOKEN_STORAGE_KEY = "omniapi_access_token";
export const REFRESH_STORAGE_KEY = "omniapi_refresh_token";
export const USER_STORAGE_KEY = "omniapi_user";
export const THEME_STORAGE_KEY = "omniapi_theme";
