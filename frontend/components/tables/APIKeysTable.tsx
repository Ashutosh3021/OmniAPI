"use client";

import Link from "next/link";
import { Trash2 } from "lucide-react";
import { useState } from "react";
import { Badge } from "@/components/shared/Badge";
import { ConfirmDialog } from "@/components/shared/ConfirmDialog";
import { EmptyState } from "@/components/shared/EmptyState";
import { formatDate } from "@/lib/utils";
import type { ApiKey } from "@/types";

interface APIKeysTableProps {
  keys: ApiKey[];
  onDelete?: (id: string | number) => void;
}

/**
 * An index list, not a table: every key is a branch off the spine, with its
 * own lamp. Hovering draws the accent rule in from the left edge.
 */
export function APIKeysTable({ keys, onDelete }: APIKeysTableProps) {
  const [pendingDelete, setPendingDelete] = useState<ApiKey | null>(null);

  if (keys.length === 0) {
    return (
      <EmptyState
        title="No API keys yet."
        description="Create one key for the application that will call the gateway. The raw key is shown once, so store it before you close the page."
      />
    );
  }

  return (
    <>
      <ul className="border-t border-ink/12">
        {keys.map((key) => (
          <li
            key={key.key_id}
            className="branch-row group flex items-center gap-3 border-b border-ink/12 py-3.5 sm:gap-4"
          >
            <Link
              href={`/api-keys/${key.key_id}`}
              className="min-w-0 flex-1"
            >
              <span className="block truncate font-medium text-ink transition-colors group-hover:text-accent">
                {key.name}
              </span>
              <span className="block truncate font-mono text-micro text-muted">
                key {key.key_id} · created {formatDate(key.created_at)}
              </span>
            </Link>

            <span className="hidden shrink-0 text-meta text-muted md:block">
              expires {key.expires_at ? formatDate(key.expires_at) : "never"}
            </span>

            <Badge tone={key.is_active ? "ok" : "bad"}>
              {key.is_active ? "active" : "revoked"}
            </Badge>

            {onDelete && (
              <button
                type="button"
                onClick={() => setPendingDelete(key)}
                className="shrink-0 rounded p-2 text-muted transition-colors hover:text-bad"
                aria-label={`Delete ${key.name}`}
              >
                <Trash2 className="h-4 w-4" aria-hidden />
              </button>
            )}
          </li>
        ))}
      </ul>

      <ConfirmDialog
        open={!!pendingDelete}
        title="Delete this API key?"
        description={`"${pendingDelete?.name}" will be deleted permanently. Any application using it will stop working immediately. This cannot be undone.`}
        confirmLabel="Delete key"
        onClose={() => setPendingDelete(null)}
        onConfirm={() => {
          if (pendingDelete && onDelete) onDelete(pendingDelete.key_id);
          setPendingDelete(null);
        }}
      />
    </>
  );
}
