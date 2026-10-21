"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Webhook } from "lucide-react";
import { Button } from "@/components/shared/Button";
import { Input } from "@/components/shared/Input";
import { Select } from "@/components/shared/Select";
import { CopyButton } from "@/components/shared/CopyButton";
import { WEBHOOK_EVENT_TYPES } from "@/lib/constants";
import { api } from "@/lib/api";
import { useNotification } from "@/context/NotificationContext";
import { webhookSchema, type WebhookInput } from "@/lib/validators";
import type { Webhook as WebhookType } from "@/types";

export function CreateWebhookForm() {
  const router = useRouter();
  const { notify } = useNotification();
  const [loading, setLoading] = useState(false);
  const [secret, setSecret] = useState<string | null>(null);

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
      const created = await api.post<WebhookType & { secret?: string }>(
        "/webhooks",
        data
      );
      if (created.secret) {
        setSecret(created.secret);
        notify("Webhook created", "success");
      } else {
        router.push("/webhooks");
      }
    } catch {
      notify("Could not create the webhook", "error");
    } finally {
      setLoading(false);
    }
  };

  if (secret) {
    return (
      <div className="flex flex-col gap-4">
        <p className="text-ui text-muted">
          This signing secret is shown once. Use it to verify the{" "}
          <code className="font-mono text-[0.8125rem] text-ink">
            X-OmniAPI-Signature
          </code>{" "}
          header on every payload.
        </p>
        <div className="code-panel flex items-start gap-3 p-3.5" aria-live="polite">
          <code className="flex-1 break-all font-mono text-[0.8125rem] text-ink">
            {secret}
          </code>
          <CopyButton value={secret} label="Copy" />
        </div>
        <div className="flex justify-end">
          <Button onClick={() => router.push("/webhooks")}>Done</Button>
        </div>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-5" noValidate>
      <Input
        label="Endpoint URL"
        type="url"
        placeholder="https://api.example.com/webhooks/omniapi"
        hint="Must be HTTPS. OmniAPI signs every delivery it sends."
        error={errors.url?.message}
        {...register("url")}
      />
      <Select
        label="Event type"
        placeholder="Choose an event"
        options={WEBHOOK_EVENT_TYPES.map((e) => ({
          value: e.value,
          label: e.label,
        }))}
        error={errors.event_type?.message}
        {...register("event_type")}
      />
      <div className="flex flex-col gap-2 border-t border-ink/12 pt-5 sm:flex-row sm:justify-end">
        <Button type="button" variant="secondary" onClick={() => router.back()}>
          Cancel
        </Button>
        <Button type="submit" loading={loading}>
          <Webhook className="h-4 w-4" aria-hidden />
          Create webhook
        </Button>
      </div>
    </form>
  );
}
