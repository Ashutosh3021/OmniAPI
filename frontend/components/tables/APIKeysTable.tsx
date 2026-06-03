"use client";

import Link from "next/link";
import { MoreHorizontal, Trash2, AlertTriangle } from "lucide-react";
import { useState } from "react";
import { Badge } from "@/components/shared/Badge";
import { formatDate } from "@/lib/utils";
import type { ApiKey } from "@/types";

interface APIKeysTableProps {
  keys: ApiKey[];
  onDelete?: (id: string | number) => void;
}

interface DeleteDialogProps {
  keyName: string;
  onConfirm: () => void;
  onCancel: () => void;
}

function DeleteConfirmDialog({ keyName, onConfirm, onCancel }: DeleteDialogProps) {
  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="delete-dialog-title"
      className="fixed inset-0 z-50 flex items-center justify-center"
    >
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50"
        onClick={onCancel}
        aria-hidden="true"
      />

      {/* Dialog panel */}
      <div className="relative bg-surface rounded-2xl shadow-xl p-xl w-full max-w-sm mx-md border border-outline">
        <div className="flex items-start gap-md mb-md">
          <span className="flex-shrink-0 p-sm bg-error-container rounded-full">
            <AlertTriangle className="h-5 w-5 text-error" aria-hidden="true" />
          </span>
          <div>
            <h2 id="delete-dialog-title" className="text-headline-sm font-semibold text-on-surface">
              Delete API Key
            </h2>
            <p className="text-body-sm text-on-surface-variant mt-xs">
              <span className="font-medium text-on-surface">&ldquo;{keyName}&rdquo;</span> will be
              permanently deleted. Any applications using this key will stop working immediately.
              This cannot be undone.
            </p>
          </div>
        </div>

        <div className="flex justify-end gap-sm mt-lg">
          <button
            type="button"
            onClick={onCancel}
            className="px-md py-sm text-label-md font-medium rounded-lg border border-outline text-on-surface hover:bg-surface-container-low transition-colors"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={onConfirm}
            className="px-md py-sm text-label-md font-medium rounded-lg bg-error text-on-error hover:opacity-90 transition-opacity"
          >
            Delete key
          </button>
        </div>
      </div>
    </div>
  );
}

export function APIKeysTable({ keys, onDelete }: APIKeysTableProps) {
  const [pendingDelete, setPendingDelete] = useState<ApiKey | null>(null);

  const handleDeleteClick = (key: ApiKey) => {
    setPendingDelete(key);
  };

  const handleConfirm = () => {
    if (pendingDelete && onDelete) {
      onDelete(pendingDelete.key_id);
    }
    setPendingDelete(null);
  };

  const handleCancel = () => {
    setPendingDelete(null);
  };

  if (keys.length === 0) {
    return (
      <p className="text-body-md text-on-surface-variant py-xl text-center">
        No API keys yet. Create your first key to get started.
      </p>
    );
  }

  return (
    <>
      {/* Confirmation dialog */}
      {pendingDelete && (
        <DeleteConfirmDialog
          keyName={pendingDelete.name}
          onConfirm={handleConfirm}
          onCancel={handleCancel}
        />
      )}

      {/* Desktop table */}
      <div className="hidden md:block overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-surface-container-low border-b border-outline">
              <th className="py-sm px-lg text-label-sm text-on-surface-variant uppercase font-semibold">Name</th>
              <th className="py-sm px-lg text-label-sm text-on-surface-variant uppercase font-semibold">Status</th>
              <th className="py-sm px-lg text-label-sm text-on-surface-variant uppercase font-semibold">Expires</th>
              <th className="py-sm px-lg text-label-sm text-on-surface-variant uppercase font-semibold">Created</th>
              <th className="py-sm px-lg text-label-sm text-on-surface-variant uppercase font-semibold">Actions</th>
            </tr>
          </thead>
          <tbody className="font-sans text-body-sm">
            {keys.map((key) => (
              <tr key={key.key_id} className="border-b border-outline-variant hover:bg-surface-container-low">
                <td className="py-md px-lg">
                  <Link href={`/api-keys/${key.key_id}`} className="text-secondary-fixed hover:underline font-medium">
                    {key.name}
                  </Link>
                </td>
                <td className="py-md px-lg">
                  <Badge variant={key.is_active ? "success" : "error"}>
                    {key.is_active ? "Active" : "Revoked"}
                  </Badge>
                </td>
                <td className="py-md px-lg text-on-surface-variant">
                  {key.expires_at ? formatDate(key.expires_at) : "Never"}
                </td>
                <td className="py-md px-lg text-on-surface-variant">
                  {formatDate(key.created_at)}
                </td>
                <td className="py-md px-lg">
                  <div className="flex gap-2">
                    <Link href={`/api-keys/${key.key_id}`} className="p-1 hover:text-secondary-fixed" aria-label={`View ${key.name}`}>
                      <MoreHorizontal className="h-4 w-4" />
                    </Link>
                    {onDelete && (
                      <button
                        type="button"
                        onClick={() => handleDeleteClick(key)}
                        className="p-1 hover:text-error"
                        aria-label={`Delete ${key.name}`}
                      >
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
          <div
            key={key.key_id}
            className="flex items-center justify-between bg-white dark:bg-surface border border-outline rounded-xl p-md hover:border-secondary-fixed"
          >
            <Link
              href={`/api-keys/${key.key_id}`}
              className="flex-1 min-w-0"
            >
              <div className="flex justify-between items-start mb-sm">
                <span className="font-medium text-on-surface truncate">{key.name}</span>
                <Badge variant={key.is_active ? "success" : "error"}>
                  {key.is_active ? "Active" : "Revoked"}
                </Badge>
              </div>
              <p className="text-label-sm text-on-surface-variant mt-sm">
                Expires: {key.expires_at ? formatDate(key.expires_at) : "Never"}
              </p>
            </Link>
            {onDelete && (
              <button
                type="button"
                onClick={() => handleDeleteClick(key)}
                className="ml-md flex-shrink-0 p-1 hover:text-error"
                aria-label={`Delete ${key.name}`}
              >
                <Trash2 className="h-4 w-4" />
              </button>
            )}
          </div>
        ))}
      </div>
    </>
  );
}
