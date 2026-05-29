import { z } from "zod";

export const loginSchema = z.object({
  email: z.string().email("Enter a valid email address"),
  password: z.string().min(6, "Password must be at least 6 characters"),
});

export const signupSchema = z
  .object({
    name: z.string().min(2, "Name must be at least 2 characters"),
    email: z.string().email("Enter a valid email address"),
    password: z.string().min(8, "Password must be at least 8 characters"),
    confirmPassword: z.string(),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "Passwords do not match",
    path: ["confirmPassword"],
  });

export const forgotPasswordSchema = z.object({
  email: z.string().email("Enter a valid email address"),
});

export const apiKeySchema = z.object({
  name: z.string().min(2, "Key name is required"),
  permissions: z
    .array(z.string())
    .min(1, "Select at least one permission"),
  expirationDate: z.string().optional(),
});

export const externalServiceSchema = z.object({
  name: z.string().min(2, "Service name is required"),
  serviceType: z.string().min(1, "Select a provider"),
  apiKey: z.string().min(1, "API key is required"),
  rateLimit: z.number().min(0).optional(),
});

export const webhookSchema = z.object({
  name: z.string().min(2, "Webhook name is required"),
  url: z.string().url("Enter a valid URL"),
  events: z.array(z.string()).min(1, "Select at least one event"),
  secret: z.string().optional(),
});

export const profileSchema = z.object({
  name: z.string().min(2),
  email: z.string().email(),
  company: z.string().optional(),
});

export const securitySchema = z
  .object({
    currentPassword: z.string().min(6),
    newPassword: z.string().min(8),
    confirmPassword: z.string(),
  })
  .refine((data) => data.newPassword === data.confirmPassword, {
    message: "Passwords do not match",
    path: ["confirmPassword"],
  });

export type LoginInput = z.infer<typeof loginSchema>;
export type SignupInput = z.infer<typeof signupSchema>;
export type ApiKeyInput = z.infer<typeof apiKeySchema>;
export type ExternalServiceInput = z.infer<typeof externalServiceSchema>;
export type WebhookInput = z.infer<typeof webhookSchema>;
export type ForgotPasswordInput = z.infer<typeof forgotPasswordSchema>;
