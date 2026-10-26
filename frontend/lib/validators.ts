import { z } from "zod";

export const apiKeySchema = z.object({
  name: z.string().min(2, "Key name is required"),
  expires_at: z.string().optional(),
});

export const externalServiceSchema = z.object({
  service_name: z.enum(["weather", "news", "stock"], {
    error: "Select a provider",
  }),
  api_key: z.string().min(1, "The provider key is required"),
  max_calls_per_hour: z
    .number()
    .int("Use a whole number of calls")
    .min(1, "At least one call per hour")
    .max(100000, "That is more calls per hour than the gateway allows")
    .optional(),
});

export const webhookSchema = z.object({
  url: z.string().url("Enter a valid URL").refine(
    (v) => v.toLowerCase().startsWith("https://"),
    "Webhook URL must use HTTPS"
  ),
  event_type: z.enum(
    ["orchestrate.complete", "orchestrate.failed", "api_key.created"],
    { error: "Select a valid event type" }
  ),
});

export type ApiKeyInput = z.infer<typeof apiKeySchema>;
export type ExternalServiceInput = z.infer<typeof externalServiceSchema>;
export type WebhookInput = z.infer<typeof webhookSchema>;
