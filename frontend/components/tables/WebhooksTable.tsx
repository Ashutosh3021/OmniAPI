"use client";

import Link from "next/link";
import { Trash2 } from "lucide-react";
import { Badge } from "@/components/shared/Badge";
import { formatRelativeTime } from "@/lib/utils";
import type { Webhook } from "@/types";

interface WebhooksTableProps {
  webhooks: Webhook[];
  onDelete?: (id: string | number) => void;
}

export function WebhooksTable({ webhooks, onDelete }: WebhooksTableProps) {
  if (webhooks.length === 0) {
    return (
      <p className="text-body-md text-on-surface-variant py-xl text-center">
        No webhooks configured.
      </p>
    );
  }

  return (
    <>
      <div className="hidden md:block overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-surface-container-low border-b border-outline">
              <th className="py-sm px-lg text-label-sm text-on-surface-variant uppercase font-semibold">URL</th>
              <th className="py-sm px-lg text-label-sm text-on-surface-variant uppercase font-semibold">Event Type</th>
              <th className="py-sm px-lg text-label-sm text-on-surface-variant uppercase font-semibold">Status</th>
              <th className="py-sm px-lg text-label-sm text-on-surface-variant uppercase font-semibold">Created</th>
              <th className="py-sm px-lg text-label-sm text-on-surface-variant uppercase font-semibold">Actions</th>
            </tr>
          </thead>
          <tbody>
            {webhooks.map((wh) => (
              <tr key={wh.webhook_id} className="border-b border-outline-variant hover:bg-surface-container-low">
                <td className="py-md px-lg">
                  <Link
                    href={`/webhooks/${wh.webhook_id}`}
                    className="font-mono text-code text-secondary-fixed hover:underline truncate max-w-[240px] block"
                  >
                    {wh.url}
                  </Link>
                </td>
                <td className="py-md px-lg text-body-sm">{wh.event_type}</td>
                <td className="py-md px-lg">
                  <Badge variant={wh.is_active ? "success" : "neutral"}>
                    {wh.is_active ? "Active" : "Paused"}
                  </Badge>
                </td>
                <td className="py-md px-lg text-body-sm text-on-surface-variant">
                  {formatRelativeTime(wh.created_at)}
                </td>
                <td className="py-md px-lg">
                  {onDelete && (
                    <button
                      type="button"
                      onClick={() => onDelete(wh.webhook_id)}
                      className="p-1 hover:text-error"
                      aria-label={`Delete webhook ${wh.webhook_id}`}
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="md:hidden space-y-md">
        {webhooks.map((wh) => (
          <Link
            key={wh.webhook_id}
            href={`/webhooks/${wh.webhook_id}`}
            className="block border border-outline rounded-xl p-md bg-white dark:bg-surface"
          >
            <div className="flex justify-between mb-sm">
              <span className="font-mono text-code text-on-surface-variant truncate">{wh.url}</span>
              <Badge variant={wh.is_active ? "success" : "neutral"}>
                {wh.is_active ? "Active" : "Paused"}
              </Badge>
            </div>
            <p className="text-body-sm text-on-surface-variant">{wh.event_type}</p>
          </Link>
        ))}
      </div>
    </>
  );
}
