"use client";

import Link from "next/link";
import { useEffect, useState, useCallback } from "react";
import { Plus } from "lucide-react";
import { APIKeysTable } from "@/components/tables/APIKeysTable";
import { PageHeader } from "@/components/shared/PageHeader";
import { Button } from "@/components/shared/Button";
import { Spinner } from "@/components/shared/Spinner";
import { Card } from "@/components/shared/Card";
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
      notify("Failed to load API keys", "error");
    }
    setLoading(false);
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
      notify("Failed to delete key", "error");
    }
  };

  return (
    <>
      <PageHeader
        title="API Keys"
        description="Manage authentication keys for your applications"
        action={
          <Link href="/api-keys/create">
            <Button>
              <Plus className="h-4 w-4" />
              Create Key
            </Button>
          </Link>
        }
      />
      <Card padding="sm">
        {loading ? <Spinner /> : <APIKeysTable keys={keys} onDelete={handleDelete} />}
      </Card>
    </>
  );
}
