"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Webhook } from "lucide-react";
import { Button } from "@/components/shared/Button";
import { Checkbox } from "@/components/shared/Checkbox";
import { Input } from "@/components/shared/Input";
import { api } from "@/lib/api";
import { useNotification } from "@/context/NotificationContext";
import { webhookSchema, type WebhookInput } from "@/lib/validators";
import type { Webhook as WebhookType } from "@/types";

const WEBHOOK_EVENTS = [
  { id: "payment.succeeded", label: "payment.succeeded" },
  { id: "payment.failed", label: "payment.failed" },
  { id: "user.created", label: "user.created" },
  { id: "api.request", label: "api.request" },
];

export function CreateWebhookForm() {
  const router = useRouter();
  const { notify } = useNotification();
  const [loading, setLoading] = useState(false);

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm<WebhookInput>({
    resolver: zodResolver(webhookSchema),
    defaultValues: { events: [] },
  });

  const events = watch("events") ?? [];

  const toggleEvent = (id: string) => {
    const next = events.includes(id)
      ? events.filter((e) => e !== id)
      : [...events, id];
    setValue("events", next, { shouldValidate: true });
  };

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
        label="Webhook Name"
        placeholder="e.g. Payment Events"
        error={errors.name?.message}
        {...register("name")}
      />
      <Input
        label="Endpoint URL"
        type="url"
        placeholder="https://api.example.com/webhooks"
        error={errors.url?.message}
        {...register("url")}
      />
      <div>
        <p className="text-label-md font-medium text-on-surface-variant mb-sm">Events</p>
        <div className="space-y-sm">
          {WEBHOOK_EVENTS.map((evt) => (
            <Checkbox
              key={evt.id}
              label={evt.label}
              checked={events.includes(evt.id)}
              onChange={() => toggleEvent(evt.id)}
            />
          ))}
        </div>
        {errors.events && (
          <p className="text-body-sm text-error mt-sm">{errors.events.message}</p>
        )}
      </div>
      <Input
        label="Signing Secret (Optional)"
        type="password"
        hint="Used to verify webhook payloads."
        {...register("secret")}
      />
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
