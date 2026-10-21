"use client";

import Link from "next/link";
import { Trash2 } from "lucide-react";
import { Badge } from "@/components/shared/Badge";
import { EmptyState } from "@/components/shared/EmptyState";
import { SERVICE_TYPES } from "@/lib/constants";
import { formatDate } from "@/lib/utils";
import type { ExternalService } from "@/types";

interface ExternalServicesTableProps {
  services: ExternalService[];
  onDelete?: (id: number) => void;
}

const toneFor = (status: string) =>
  status === "active" ? "ok" : status === "error" ? "bad" : "neutral";

/** A gallery wall of connected providers, each one a panel on the board. */
export function ExternalServicesTable({
  services,
  onDelete,
}: ExternalServicesTableProps) {
  const label = (value: string) =>
    SERVICE_TYPES.find((s) => s.value === value)?.label ?? value;

  if (services.length === 0) {
    return (
      <EmptyState
        title="No external services connected."
        description="Add a provider key and OmniAPI will call it on your behalf. The key is encrypted at rest and never appears in a response."
      />
    );
  }

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
      {services.map((svc) => (
        <article key={svc.service_id} className="branch-row panel flex flex-col p-5">
          <div className="mb-4 flex items-start justify-between gap-3">
            <div className="min-w-0">
              <Link
                href={`/external-services/${svc.service_id}`}
                className="t-subhead block truncate font-mono text-ink transition-colors hover:text-accent"
              >
                {svc.service_name}
              </Link>
              <p className="mt-1 truncate text-meta text-muted">
                {label(svc.service_name)}
              </p>
            </div>
            <Badge tone={toneFor(svc.status)}>{svc.status}</Badge>
          </div>

          <dl className="mt-auto space-y-1.5 border-t border-ink/12 pt-3 text-meta">
            <div className="flex justify-between gap-3">
              <dt className="text-muted">Calls per hour</dt>
              <dd className="num text-ink">
                {svc.max_calls_per_hour.toLocaleString()}
              </dd>
            </div>
            <div className="flex justify-between gap-3">
              <dt className="text-muted">Connected</dt>
              <dd className="text-ink">{formatDate(svc.created_at)}</dd>
            </div>
          </dl>

          {onDelete && (
            <div className="mt-4 flex justify-end">
              <button
                type="button"
                onClick={() => onDelete(svc.service_id)}
                className="inline-flex items-center gap-1.5 rounded px-2 py-1.5 text-meta text-muted transition-colors hover:text-bad"
                aria-label={`Remove ${svc.service_name}`}
              >
                <Trash2 className="h-3.5 w-3.5" aria-hidden />
                Remove
              </button>
            </div>
          )}
        </article>
      ))}
    </div>
  );
}
