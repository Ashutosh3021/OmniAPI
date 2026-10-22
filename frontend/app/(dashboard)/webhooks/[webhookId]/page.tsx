"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Send } from "lucide-react";
import { PageHeader } from "@/components/shared/PageHeader";
import { Badge } from "@/components/shared/Badge";
import { Button } from "@/components/shared/Button";
import { Spinner } from "@/components/shared/Spinner";
import { ConfirmDialog } from "@/components/shared/ConfirmDialog";
import { EmptyState } from "@/components/shared/EmptyState";
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
  const [notFound, setNotFound] = useState(false);
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [sending, setSending] = useState(false);

  useEffect(() => {
    let cancelled = false;
    api
      .get<Webhook>(`/webhooks/${webhookId}`)
      .then((data) => {
        if (!cancelled) setWebhook(data);
      })
      .catch(() => {
        if (!cancelled) setNotFound(true);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [webhookId]);

  const sendTest = async () => {
    setSending(true);
    try {
      await api.post(`/webhooks/${webhookId}/test`);
      notify("Test ping queued", "success");
    } catch {
      notify("The test ping could not be sent", "error");
    } finally {
      setSending(false);
    }
  };

  const onDelete = async () => {
    setConfirmOpen(false);
    try {
      await api.delete(`/webhooks/${webhookId}`);
      notify("Webhook deleted", "success");
      router.push("/webhooks");
    } catch {
      notify("Could not delete the webhook", "error");
    }
  };

  if (loading) return <Spinner full label="Loading webhook" />;

  if (notFound || !webhook) {
    return (
      <>
        <PageHeader title="Webhook not found" />
        <EmptyState
          title="This webhook does not exist."
          description="It may have been deleted, or the link may be wrong."
        />
      </>
    );
  }

  const deliveries = webhook.recent_events ?? [];

  return (
    <div className="max-w-2xl">
      <PageHeader
        meta={webhook.event_type}
        title="Webhook"
        description={webhook.url}
        action={
          <div className="flex flex-wrap items-center gap-2">
            <Badge tone={webhook.is_active ? "ok" : "neutral"}>
              {webhook.is_active ? "active" : "paused"}
            </Badge>
            <Badge tone="accent">{webhook.event_type}</Badge>
          </div>
        }
      />

      <div className="panel p-5 md:p-7">
        <dl className="space-y-2.5 text-ui">
          <div className="flex justify-between gap-4">
            <dt className="text-muted">Created</dt>
            <dd className="text-ink">{formatDate(webhook.created_at)}</dd>
          </div>
          <div className="flex justify-between gap-4">
            <dt className="text-muted">Retries so far</dt>
            <dd className="num text-ink">{webhook.retry_count}</dd>
          </div>
        </dl>

        <div className="mt-6 flex flex-col gap-2 border-t border-ink/12 pt-5 sm:flex-row sm:justify-between">
          <Button variant="danger" onClick={() => setConfirmOpen(true)}>
            Delete webhook
          </Button>
          <Button
            variant="secondary"
            onClick={sendTest}
            loading={sending}
            disabled={!webhook.is_active}
          >
            <Send className="h-4 w-4" aria-hidden />
            Send test ping
          </Button>
        </div>
      </div>

      <section className="panel mt-6 p-5 md:p-7">
        <h2 className="t-subhead mb-4 text-ink">Recent deliveries</h2>
        {deliveries.length === 0 ? (
          <p className="text-ui text-muted">
            Nothing has been delivered to this endpoint yet.
          </p>
        ) : (
          <ul className="border-t border-ink/12">
            {deliveries.map((d) => (
              <li
                key={d.event_id}
                className="flex flex-wrap items-center gap-x-3 gap-y-1 border-b border-ink/12 py-2.5 last:border-0"
              >
                <span className="font-mono text-[0.8125rem] text-ink">
                  {d.event_type}
                </span>
                <Badge tone={d.status === "delivered" ? "ok" : "bad"}>
                  {d.status}
                </Badge>
                {d.http_status_code !== null && (
                  <span className="num text-meta text-muted">
                    HTTP {d.http_status_code}
                  </span>
                )}
                <span className="text-meta text-muted">
                  {d.delivered_at
                    ? formatDate(d.delivered_at)
                    : "not delivered"}
                </span>
              </li>
            ))}
          </ul>
        )}
      </section>

      <ConfirmDialog
        open={confirmOpen}
        title="Delete this webhook?"
        description="The subscription is removed immediately and your endpoint stops receiving events. This cannot be undone."
        confirmLabel="Delete webhook"
        onClose={() => setConfirmOpen(false)}
        onConfirm={onDelete}
      />
    </div>
  );
}
