"use client";

import { useEffect, useState, useCallback } from "react";
import { Plus } from "lucide-react";
import { APIKeysTable } from "@/components/tables/APIKeysTable";
import { PageHeader } from "@/components/shared/PageHeader";
import { ButtonLink } from "@/components/shared/Button";
import { Spinner } from "@/components/shared/Spinner";
import { api } from "@/lib/api";
import { useNotification } from "@/context/NotificationContext";
import type { ApiKey } from "@/types";

export default function ApiKeysPage() {
  const [keys, setKeys] = useState<ApiKey[]>([]);
  const [loading, setLoading] = useState(true);
  const { notify } = useNotification();

  const loadKeys = useCallback(async () => {
    setLoading(true);
    try {
      const data = await api.get<ApiKey[]>("/api-keys");
      setKeys(data);
    } catch {
      notify("Could not load your API keys", "error");
    } finally {
      setLoading(false);
    }
  }, [notify]);

  useEffect(() => {
    loadKeys();
  }, [loadKeys]);

  const handleDelete = async (id: string | number) => {
    try {
      await api.delete(`/api-keys/${id}`);
      notify("API key deleted", "success");
      loadKeys();
    } catch {
      notify("Could not delete that key", "error");
    }
  };

  return (
    <>
      <PageHeader
        meta={loading ? undefined : `${keys.length} ${keys.length === 1 ? "key" : "keys"}`}
        title="API keys"
        description="One key per application. Each one carries its own permissions and an optional expiry date."
        action={
          <ButtonLink href="/api-keys/create" size="sm">
            <Plus className="h-4 w-4" aria-hidden />
            Create key
          </ButtonLink>
        }
      />

      {loading ? (
        <Spinner label="Loading keys" />
      ) : (
        <APIKeysTable keys={keys} onDelete={handleDelete} />
      )}
    </>
  );
}
