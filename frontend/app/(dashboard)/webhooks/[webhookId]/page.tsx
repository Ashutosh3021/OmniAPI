"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { PageHeader } from "@/components/shared/PageHeader";
import { Card } from "@/components/shared/Card";
import { Badge } from "@/components/shared/Badge";
import { Button } from "@/components/shared/Button";
import { Spinner } from "@/components/shared/Spinner";
import { api } from "@/lib/api";
import { useNotification } from "@/context/NotificationContext";
import { formatDate } from "@/lib/utils";
import type { Webhook } from "@/types";

export default function WebhookDetailPage() {
  const { webhookId } = useParams<{ webhookId: string }>();
  const router = useRouter();
  const { notify } = useNotification();
  const [webhook, setWebhook] = useState<Webhook | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get<Webhook>(`/webhooks/${webhookId}`)
      .then(setWebhook)
      .finally(() => setLoading(false));
  }, [webhookId]);

  const onDelete = async () => {
    try {
      await api.delete(`/webhooks/${webhookId}`);
      notify("Webhook deleted", "success");
      router.push("/webhooks");
    } catch {
      notify("Failed to delete webhook", "error");
    }
  };

  if (loading) return <Spinner />;
  if (!webhook) return <p>Webhook not found</p>;

  return (
    <div className="max-w-2xl mx-auto">
      <PageHeader title={webhook.url} description={`Event: ${webhook.event_type}`} />
      <Card>
        <div className="flex gap-sm mb-md">
          <Badge variant={webhook.is_active ? "success" : "neutral"}>
            {webhook.is_active ? "Active" : "Paused"}
          </Badge>
          <Badge variant="info">{webhook.event_type}</Badge>
        </div>
        <dl className="space-y-sm text-body-sm text-on-surface-variant mb-lg">
          <div>Created {formatDate(webhook.created_at)}</div>
          <div>Retry count: {webhook.retry_count}</div>
        </dl>
        <Button variant="danger" onClick={onDelete}>
          Delete Webhook
        </Button>
      </Card>
    </div>
  );
}
