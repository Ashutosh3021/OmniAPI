"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { PageHeader } from "@/components/shared/PageHeader";
import { Input } from "@/components/shared/Input";
import { Button } from "@/components/shared/Button";
import { Spinner } from "@/components/shared/Spinner";
import { Badge } from "@/components/shared/Badge";
import { ConfirmDialog } from "@/components/shared/ConfirmDialog";
import { EmptyState } from "@/components/shared/EmptyState";
import { api } from "@/lib/api";
import { apiKeySchema, type ApiKeyInput } from "@/lib/validators";
import { useNotification } from "@/context/NotificationContext";
import { formatDate } from "@/lib/utils";
import type { ApiKey } from "@/types";

export default function ApiKeyDetailPage() {
  const { keyId } = useParams<{ keyId: string }>();
  const router = useRouter();
  const { notify } = useNotification();
  const [key, setKey] = useState<ApiKey | null>(null);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);
  const [confirmOpen, setConfirmOpen] = useState(false);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<ApiKeyInput>({
    resolver: zodResolver(apiKeySchema),
  });

  useEffect(() => {
    let cancelled = false;
    api
      .get<ApiKey>(`/api-keys/${keyId}`)
      .then((data) => {
        if (cancelled) return;
        setKey(data);
        reset({
          name: data.name,
          expires_at: data.expires_at?.split("T")[0] ?? "",
        });
      })
      .catch(() => {
        if (!cancelled) setNotFound(true);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [keyId, reset]);

  const onSave = async (data: ApiKeyInput) => {
    try {
      const payload: { name: string; expires_at?: string | null } = {
        name: data.name,
        expires_at: data.expires_at
          ? new Date(data.expires_at).toISOString()
          : null,
      };
      const updated = await api.patch<ApiKey>(`/api-keys/${keyId}`, payload);
      setKey(updated);
      notify("Key updated", "success");
    } catch {
      notify("Could not update the key", "error");
    }
  };

  const onDelete = async () => {
    setConfirmOpen(false);
    try {
      await api.delete(`/api-keys/${keyId}`);
      notify("API key deleted", "success");
      router.push("/api-keys");
    } catch {
      notify("Could not delete the key", "error");
    }
  };

  if (loading) return <Spinner full label="Loading key" />;

  if (notFound || !key) {
    return (
      <>
        <PageHeader title="Key not found" />
        <EmptyState
          title="This key does not exist."
          description="It may have been deleted, or the link may be wrong."
        />
      </>
    );
  }

  return (
    <div className="max-w-2xl">
      <PageHeader
        meta={`key ${key.key_id}`}
        title={key.name}
        description={`Key ${key.key_id} · created ${formatDate(key.created_at)}`}
        action={
          <Badge tone={key.is_active ? "ok" : "bad"}>
            {key.is_active ? "active" : "revoked"}
          </Badge>
        }
      />

      <div className="panel p-5 md:p-7">
        <form onSubmit={handleSubmit(onSave)} className="flex flex-col gap-5" noValidate>
          <Input
            label="Key name"
            error={errors.name?.message}
            {...register("name")}
          />
          <Input
            label="Expiry date"
            type="date"
            hint="Leave it empty and the key never expires."
            error={errors.expires_at?.message}
            {...register("expires_at")}
          />
          <div className="flex flex-col gap-2 border-t border-ink/12 pt-5 sm:flex-row sm:justify-between">
            <Button type="button" variant="danger" onClick={() => setConfirmOpen(true)}>
              Delete key
            </Button>
            <Button type="submit">Save changes</Button>
          </div>
        </form>
      </div>

      <ConfirmDialog
        open={confirmOpen}
        title="Delete this API key?"
        description={`"${key.name}" will be deleted permanently. Any application using it will stop working immediately. This cannot be undone.`}
        confirmLabel="Delete key"
        onClose={() => setConfirmOpen(false)}
        onConfirm={onDelete}
      />
    </div>
  );
}
