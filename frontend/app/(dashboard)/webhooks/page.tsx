"use client";

import Link from "next/link";
import { useEffect, useState, useCallback } from "react";
import { Plus } from "lucide-react";
import { WebhooksTable } from "@/components/tables/WebhooksTable";
import { PageHeader } from "@/components/shared/PageHeader";
import { Button } from "@/components/shared/Button";
import { Spinner } from "@/components/shared/Spinner";
import { Card } from "@/components/shared/Card";
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
      notify("Failed to load webhooks", "error");
    }
    setLoading(false);
  }, [notify]);

  useEffect(() => {
    load();
  }, [load]);

  const handleDelete = async (id: string) => {
    try {
      await api.delete(`/webhooks/${id}`);
      notify("Webhook deleted", "success");
      load();
    } catch {
      notify("Failed to delete webhook", "error");
    }
  };

  return (
    <>
      <PageHeader
        title="Webhooks"
        description="Receive real-time notifications for API events"
        action={
          <Link href="/webhooks/create">
            <Button>
              <Plus className="h-4 w-4" />
              Create Webhook
            </Button>
          </Link>
        }
      />
      <Card padding="sm">
        {loading ? <Spinner /> : <WebhooksTable webhooks={webhooks} onDelete={handleDelete} />}
      </Card>
    </>
  );
}
