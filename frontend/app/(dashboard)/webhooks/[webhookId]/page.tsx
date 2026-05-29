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
import { formatDate, formatRelativeTime } from "@/lib/utils";
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
      <PageHeader title={webhook.name} description={webhook.url} />
      <Card>
        <div className="flex gap-sm mb-md">
          <Badge variant="success">{webhook.status}</Badge>
          <Badge variant="info">{webhook.successRate}% success</Badge>
        </div>
        <div className="mb-md">
          <p className="text-label-md text-on-surface-variant mb-sm">Events</p>
          <div className="flex flex-wrap gap-sm">
            {webhook.events.map((e) => (
              <Badge key={e} variant="neutral">
                {e}
              </Badge>
            ))}
          </div>
        </div>
        <dl className="space-y-sm text-body-sm text-on-surface-variant mb-lg">
          <div>Created {formatDate(webhook.createdAt)}</div>
          <div>
            Last triggered{" "}
            {webhook.lastTriggered
              ? formatRelativeTime(webhook.lastTriggered)
              : "Never"}
          </div>
        </dl>
        <Button variant="danger" onClick={onDelete}>
          Delete Webhook
        </Button>
      </Card>
    </div>
  );
}
