"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { PageHeader } from "@/components/shared/PageHeader";
import { Card } from "@/components/shared/Card";
import { Input } from "@/components/shared/Input";
import { Button } from "@/components/shared/Button";
import { Spinner } from "@/components/shared/Spinner";
import { Badge } from "@/components/shared/Badge";
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

  const { register, handleSubmit, reset, formState: { errors } } = useForm<ApiKeyInput>({
    resolver: zodResolver(apiKeySchema),
  });

  useEffect(() => {
    api.get<ApiKey>(`/api-keys/${keyId}`).then((data) => {
      setKey(data);
      reset({
        name: data.name,
        expires_at: data.expires_at?.split("T")[0] ?? "",
      });
      setLoading(false);
    }).catch(() => setLoading(false));
  }, [keyId, reset]);

  const onSave = async (data: ApiKeyInput) => {
    try {
      const payload: { name: string; expires_at?: string } = { name: data.name };
      if (data.expires_at) {
        payload.expires_at = new Date(data.expires_at).toISOString();
      }
      await api.patch(`/api-keys/${keyId}`, payload);
      notify("API key updated", "success");
    } catch {
      notify("Failed to update key", "error");
    }
  };

  const onDelete = async () => {
    try {
      await api.delete(`/api-keys/${keyId}`);
      notify("API key permanently deleted", "success");
      router.push("/api-keys");
    } catch {
      notify("Failed to delete key", "error");
    }
  };

  if (loading) return <Spinner />;
  if (!key) return <p>Key not found</p>;

  return (
    <div className="max-w-2xl mx-auto">
      <PageHeader title={key.name} description={`Key ID: ${key.key_id}`} />
      <Card className="mb-lg">
        <div className="flex gap-sm mb-md">
          <Badge variant={key.is_active ? "success" : "error"}>
            {key.is_active ? "Active" : "Revoked"}
          </Badge>
          <span className="text-body-sm text-on-surface-variant">
            Created {formatDate(key.created_at)}
          </span>
        </div>
        <form onSubmit={handleSubmit(onSave)} className="space-y-lg">
          <Input label="Key Name" error={errors.name?.message} {...register("name")} />
          <Input label="Expiration Date (Optional)" type="date" {...register("expires_at")} />
          <div className="flex gap-md">
            <Button type="submit">Save Changes</Button>
            <Button type="button" variant="danger" onClick={onDelete}>
              Delete Key
            </Button>
          </div>
        </form>
      </Card>
    </div>
  );
}
