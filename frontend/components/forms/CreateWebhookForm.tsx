"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Webhook } from "lucide-react";
import { Button } from "@/components/shared/Button";
import { Input } from "@/components/shared/Input";
import { api } from "@/lib/api";
import { useNotification } from "@/context/NotificationContext";
import { webhookSchema, type WebhookInput } from "@/lib/validators";
import type { Webhook as WebhookType } from "@/types";

const WEBHOOK_EVENT_TYPES = [
  { value: "orchestrate.complete", label: "Orchestrate — Complete" },
  { value: "orchestrate.failed", label: "Orchestrate — Failed" },
  { value: "api_key.created", label: "API Key — Created" },
] as const;

export function CreateWebhookForm() {
  const router = useRouter();
  const { notify } = useNotification();
  const [loading, setLoading] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<WebhookInput>({
    resolver: zodResolver(webhookSchema),
  });

  const onSubmit = async (data: WebhookInput) => {
    setLoading(true);
    try {
      await api.post<WebhookType>("/webhooks", data);
      notify("Webhook created successfully", "success");
      router.push("/webhooks");
    } catch {
      notify("Failed to create webhook", "error");
    }
    setLoading(false);
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-xl" noValidate>
      <Input
        label="Endpoint URL"
        type="url"
        placeholder="https://api.example.com/webhooks"
        hint="Must be an HTTPS URL."
        error={errors.url?.message}
        {...register("url")}
      />
      <div>
        <label className="text-label-md font-medium text-on-surface-variant mb-sm block">
          Event Type
        </label>
        <select
          className="w-full rounded border border-outline bg-surface px-md py-sm text-body-md text-on-surface focus:outline-none focus:ring-2 focus:ring-secondary-fixed"
          {...register("event_type")}
        >
          <option value="">Select an event…</option>
          {WEBHOOK_EVENT_TYPES.map((evt) => (
            <option key={evt.value} value={evt.value}>
              {evt.label}
            </option>
          ))}
        </select>
        {errors.event_type && (
          <p className="text-body-sm text-error mt-sm" role="alert">
            {errors.event_type.message}
          </p>
        )}
      </div>
      <div className="flex flex-col sm:flex-row justify-end gap-md pt-lg border-t border-outline-variant">
        <Button type="button" variant="secondary" onClick={() => router.back()}>
          Cancel
        </Button>
        <Button type="submit" loading={loading}>
          <Webhook className="h-4 w-4" />
          Create Webhook
        </Button>
      </div>
    </form>
  );
}
