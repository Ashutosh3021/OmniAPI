"use client";

import Link from "next/link";
import { MoreHorizontal, Trash2 } from "lucide-react";
import { Badge } from "@/components/shared/Badge";
import { maskKey, formatDate, formatRelativeTime } from "@/lib/utils";
import type { ApiKey } from "@/types";

interface APIKeysTableProps {
  keys: ApiKey[];
  onDelete?: (id: string) => void;
}

export function APIKeysTable({ keys, onDelete }: APIKeysTableProps) {
  if (keys.length === 0) {
    return (
      <p className="text-body-md text-on-surface-variant py-xl text-center">
        No API keys yet. Create your first key to get started.
      </p>
    );
  }

  return (
    <>
      {/* Desktop table */}
      <div className="hidden md:block overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-surface-container-low border-b border-outline">
              <th className="py-sm px-lg text-label-sm text-on-surface-variant uppercase font-semibold">Name</th>
              <th className="py-sm px-lg text-label-sm text-on-surface-variant uppercase font-semibold">Key</th>
              <th className="py-sm px-lg text-label-sm text-on-surface-variant uppercase font-semibold">Permissions</th>
              <th className="py-sm px-lg text-label-sm text-on-surface-variant uppercase font-semibold">Status</th>
              <th className="py-sm px-lg text-label-sm text-on-surface-variant uppercase font-semibold">Last Used</th>
              <th className="py-sm px-lg text-label-sm text-on-surface-variant uppercase font-semibold">Actions</th>
            </tr>
          </thead>
          <tbody className="font-mono text-code">
            {keys.map((key) => (
              <tr key={key.id} className="border-b border-outline-variant hover:bg-surface-container-low">
                <td className="py-md px-lg font-sans text-body-md">
                  <Link href={`/api-keys/${key.id}`} className="text-secondary-fixed hover:underline">
                    {key.name}
                  </Link>
                </td>
                <td className="py-md px-lg text-on-surface-variant">{maskKey(key.key)}</td>
                <td className="py-md px-lg font-sans text-body-sm">{key.permissions.join(", ")}</td>
                <td className="py-md px-lg">
                  <Badge variant={key.status === "active" ? "success" : key.status === "expiring" ? "warning" : "error"}>
                    {key.status}
                  </Badge>
                </td>
                <td className="py-md px-lg font-sans text-body-sm text-on-surface-variant">
                  {key.lastUsed ? formatRelativeTime(key.lastUsed) : "Never"}
                </td>
                <td className="py-md px-lg">
                  <div className="flex gap-2">
                    <Link href={`/api-keys/${key.id}`} className="p-1 hover:text-secondary-fixed" aria-label={`View ${key.name}`}>
                      <MoreHorizontal className="h-4 w-4" />
                    </Link>
                    {onDelete && (
                      <button type="button" onClick={() => onDelete(key.id)} className="p-1 hover:text-error" aria-label={`Delete ${key.name}`}>
                        <Trash2 className="h-4 w-4" />
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Mobile cards */}
      <div className="md:hidden space-y-md">
        {keys.map((key) => (
          <Link
            key={key.id}
            href={`/api-keys/${key.id}`}
            className="block bg-white dark:bg-surface border border-outline rounded-xl p-md hover:border-secondary-fixed"
          >
            <div className="flex justify-between items-start mb-sm">
              <span className="font-medium text-on-surface">{key.name}</span>
              <Badge variant={key.status === "active" ? "success" : "warning"}>{key.status}</Badge>
            </div>
            <p className="font-mono text-code text-on-surface-variant">{maskKey(key.key)}</p>
            <p className="text-label-sm text-on-surface-variant mt-sm">
              Expires: {key.expiresAt ? formatDate(key.expiresAt) : "Never"}
            </p>
          </Link>
        ))}
      </div>
    </>
  );
}
