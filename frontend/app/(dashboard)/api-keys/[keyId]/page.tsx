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
import { maskKey, formatDate } from "@/lib/utils";
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
        permissions: data.permissions,
        expirationDate: data.expiresAt?.split("T")[0] ?? "",
      });
      setLoading(false);
    }).catch(() => setLoading(false));
  }, [keyId, reset]);

  const onSave = async (data: ApiKeyInput) => {
    try {
      await api.put(`/api-keys/${keyId}`, data);
      notify("API key updated", "success");
    } catch {
      notify("Failed to update key", "error");
    }
  };

  const onDelete = async () => {
    try {
      await api.delete(`/api-keys/${keyId}`);
      notify("API key revoked", "success");
      router.push("/api-keys");
    } catch {
      notify("Failed to delete key", "error");
    }
  };

  if (loading) return <Spinner />;
  if (!key) return <p>Key not found</p>;

  return (
    <div className="max-w-2xl mx-auto">
      <PageHeader title={key.name} description={`Key: ${maskKey(key.key)}`} />
      <Card className="mb-lg">
        <div className="flex gap-sm mb-md">
          <Badge variant={key.status === "active" ? "success" : "warning"}>{key.status}</Badge>
          <span className="text-body-sm text-on-surface-variant">
            Created {formatDate(key.createdAt)}
          </span>
        </div>
        <form onSubmit={handleSubmit(onSave)} className="space-y-lg">
          <Input label="Key Name" error={errors.name?.message} {...register("name")} />
          <Input label="Expiration" type="date" {...register("expirationDate")} />
          <div className="flex gap-md">
            <Button type="submit">Save Changes</Button>
            <Button type="button" variant="danger" onClick={onDelete}>
              Revoke Key
            </Button>
          </div>
        </form>
      </Card>
    </div>
  );
}
