/**
 * Backend API base URL
 * - Development: http://localhost:8000/api/v1
 * - Production: Set NEXT_PUBLIC_API_URL environment variable
 */
export const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export const NAV_ITEMS = [
  { href: "/dashboard", label: "Dashboard", icon: "LayoutDashboard" },
  { href: "/api-keys", label: "API Keys", icon: "Key" },
  {
    href: "/external-services",
    label: "External Services",
    icon: "Plug",
  },
  { href: "/orchestrate", label: "Orchestrate", icon: "GitBranch" },
  { href: "/analytics", label: "Analytics", icon: "BarChart3" },
  { href: "/webhooks", label: "Webhooks", icon: "Webhook" },
  { href: "/settings", label: "Settings", icon: "Settings" },
] as const;

export const MOBILE_NAV_ITEMS = [
  { href: "/dashboard", label: "Home", icon: "Home" },
  { href: "/api-keys", label: "API", icon: "Key" },
  { href: "/orchestrate", label: "Flows", icon: "GitBranch" },
  { href: "/docs", label: "Docs", icon: "BookOpen" },
] as const;

export const API_KEY_PERMISSIONS = [
  { id: "read", label: "Read" },
  { id: "write", label: "Write" },
  { id: "delete", label: "Delete" },
  { id: "admin", label: "Admin" },
] as const;

export const SERVICE_TYPES = [
  { value: "stripe", label: "Stripe Payment Gateway" },
  { value: "twilio", label: "Twilio SMS/Voice" },
  { value: "sendgrid", label: "SendGrid Email" },
  { value: "aws_s3", label: "AWS S3 Storage" },
  { value: "custom", label: "Custom Webhook" },
] as const;

export const HTTP_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE"] as const;

export const DOCS_SECTIONS = [
  { id: "getting-started", title: "Getting Started" },
  { id: "authentication", title: "Authentication" },
  { id: "api-reference", title: "API Reference" },
  { id: "webhooks", title: "Webhooks" },
  { id: "code-examples", title: "Code Examples" },
] as const;

export const TOKEN_STORAGE_KEY = "omniapi_access_token";
export const REFRESH_STORAGE_KEY = "omniapi_refresh_token";
export const USER_STORAGE_KEY = "omniapi_user";
