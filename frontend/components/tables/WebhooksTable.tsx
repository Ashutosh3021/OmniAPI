"use client";

import Link from "next/link";
import { Trash2 } from "lucide-react";
import { Badge } from "@/components/shared/Badge";
import { formatRelativeTime } from "@/lib/utils";
import type { Webhook } from "@/types";

interface WebhooksTableProps {
  webhooks: Webhook[];
  onDelete?: (id: string) => void;
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
              <th className="py-sm px-lg text-label-sm text-on-surface-variant uppercase font-semibold">Name</th>
              <th className="py-sm px-lg text-label-sm text-on-surface-variant uppercase font-semibold">URL</th>
              <th className="py-sm px-lg text-label-sm text-on-surface-variant uppercase font-semibold">Events</th>
              <th className="py-sm px-lg text-label-sm text-on-surface-variant uppercase font-semibold">Success</th>
              <th className="py-sm px-lg text-label-sm text-on-surface-variant uppercase font-semibold">Last Triggered</th>
              <th className="py-sm px-lg text-label-sm text-on-surface-variant uppercase font-semibold">Actions</th>
            </tr>
          </thead>
          <tbody>
            {webhooks.map((wh) => (
              <tr key={wh.id} className="border-b border-outline-variant hover:bg-surface-container-low">
                <td className="py-md px-lg">
                  <Link href={`/webhooks/${wh.id}`} className="text-secondary-fixed hover:underline font-medium">
                    {wh.name}
                  </Link>
                </td>
                <td className="py-md px-lg font-mono text-code text-on-surface-variant truncate max-w-[200px]">
                  {wh.url}
                </td>
                <td className="py-md px-lg text-body-sm">{wh.events.length} events</td>
                <td className="py-md px-lg">
                  <Badge variant="success">{wh.successRate}%</Badge>
                </td>
                <td className="py-md px-lg text-body-sm text-on-surface-variant">
                  {wh.lastTriggered ? formatRelativeTime(wh.lastTriggered) : "Never"}
                </td>
                <td className="py-md px-lg">
                  {onDelete && (
                    <button type="button" onClick={() => onDelete(wh.id)} className="p-1 hover:text-error" aria-label={`Delete ${wh.name}`}>
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
          <Link key={wh.id} href={`/webhooks/${wh.id}`} className="block border border-outline rounded-xl p-md bg-white dark:bg-surface">
            <div className="flex justify-between mb-sm">
              <span className="font-medium">{wh.name}</span>
              <Badge variant="success">{wh.status}</Badge>
            </div>
            <p className="font-mono text-code text-on-surface-variant truncate">{wh.url}</p>
          </Link>
        ))}
      </div>
    </>
  );
}
