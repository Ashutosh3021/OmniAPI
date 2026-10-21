"use client";

import { useEffect, useState, useCallback } from "react";
import { Plus } from "lucide-react";
import { WebhooksTable } from "@/components/tables/WebhooksTable";
import { PageHeader } from "@/components/shared/PageHeader";
import { ButtonLink } from "@/components/shared/Button";
import { Spinner } from "@/components/shared/Spinner";
import { api } from "@/lib/api";
import { useNotification } from "@/context/NotificationContext";
import type { Webhook } from "@/types";

export default function WebhooksPage() {
  const [webhooks, setWebhooks] = useState<Webhook[]>([]);
  const [loading, setLoading] = useState(true);
  const { notify } = useNotification();

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setWebhooks(await api.get<Webhook[]>("/webhooks"));
    } catch {
      notify("Could not load your webhooks", "error");
    } finally {
      setLoading(false);
    }
  }, [notify]);

  useEffect(() => {
    load();
  }, [load]);

  const handleDelete = async (id: string | number) => {
    try {
      await api.delete(`/webhooks/${id}`);
      notify("Webhook deleted", "success");
      load();
    } catch {
      notify("Could not delete that webhook", "error");
    }
  };

  return (
    <>
      <PageHeader
        meta={loading ? undefined : `${webhooks.length} subscriptions`}
        title="Webhooks"
        description="Push events to your own server instead of polling for them. Failed deliveries retry with exponential backoff."
        action={
          <ButtonLink href="/webhooks/create" size="sm">
            <Plus className="h-4 w-4" aria-hidden />
            Add webhook
          </ButtonLink>
        }
      />

      {loading ? (
        <Spinner label="Loading webhooks" />
      ) : (
        <WebhooksTable webhooks={webhooks} onDelete={handleDelete} />
      )}
    </>
  );
}
