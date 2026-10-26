"use client";

import Link from "next/link";
import { Trash2 } from "lucide-react";
import { Badge } from "@/components/shared/Badge";
import { EmptyState } from "@/components/shared/EmptyState";
import { formatRelativeTime } from "@/lib/utils";
import type { Webhook } from "@/types";

interface WebhooksTableProps {
  webhooks: Webhook[];
  onDelete?: (id: string | number) => void;
}

export function WebhooksTable({ webhooks, onDelete }: WebhooksTableProps) {
  if (webhooks.length === 0) {
    return (
      <EmptyState
        title="No webhooks configured."
        description="Subscribe to an event and OmniAPI will push it to your server the moment it happens, with retries when a delivery fails."
      />
    );
  }

  return (
    <ul className="border-t border-ink/12">
      {webhooks.map((wh) => (
        <li
          key={wh.webhook_id}
          className="branch-row group flex items-center gap-3 border-b border-ink/12 py-3.5 sm:gap-4"
        >
          <Link href={`/webhooks/${wh.webhook_id}`} className="min-w-0 flex-1">
            <span className="block truncate font-mono text-[0.8125rem] text-ink transition-colors group-hover:text-accent group-hover:translate-x-0.5 transition-transform">
              {wh.url}
            </span>
            <span className="mt-1 block truncate font-mono text-micro text-muted">
              {wh.event_type} · created {formatRelativeTime(wh.created_at)}
            </span>
          </Link>

          <Badge tone={wh.is_active ? "ok" : "neutral"}>
            {wh.is_active ? "active" : "paused"}
          </Badge>

          {onDelete && (
            <button
              type="button"
              onClick={() => onDelete(wh.webhook_id)}
              className="shrink-0 rounded p-2 text-muted transition-all hover:text-bad hover:scale-110"
              aria-label={`Delete webhook ${wh.webhook_id}`}
            >
              <Trash2 className="h-4 w-4" aria-hidden />
            </button>
          )}
        </li>
      ))}
    </ul>
  );
}
