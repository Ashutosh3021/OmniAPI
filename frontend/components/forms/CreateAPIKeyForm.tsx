"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Key } from "lucide-react";
import { Button } from "@/components/shared/Button";
import { Input } from "@/components/shared/Input";
import { CopyButton } from "@/components/shared/CopyButton";
import { api } from "@/lib/api";
import { useNotification } from "@/context/NotificationContext";
import { apiKeySchema, type ApiKeyInput } from "@/lib/validators";
import type { ApiKey } from "@/types";

export function CreateAPIKeyForm() {
  const router = useRouter();
  const { notify } = useNotification();
  const [loading, setLoading] = useState(false);
  const [generatedKey, setGeneratedKey] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ApiKeyInput>({
    resolver: zodResolver(apiKeySchema),
  });

  const onSubmit = async (data: ApiKeyInput) => {
    setLoading(true);
    try {
      const payload: { name: string; expires_at?: string } = { name: data.name };
      if (data.expires_at) {
        payload.expires_at = new Date(data.expires_at).toISOString();
      }

      const result = await api.post<ApiKey & { raw_key: string }>(
        "/api-keys",
        payload
      );
      if (result.raw_key) {
        setGeneratedKey(result.raw_key);
        notify("Key created", "success");
      } else {
        notify("The key was created but the secret was not returned", "error");
      }
    } catch {
      notify("Could not create the key", "error");
    } finally {
      setLoading(false);
    }
  };

  if (generatedKey) {
    return (
      <div className="flex flex-col gap-4">
        <p className="text-ui text-muted">
          Copy this key now. It is shown once and cannot be retrieved again.
        </p>
        <div
          className="code-panel flex items-start gap-3 p-3.5"
          aria-live="polite"
        >
          <code className="flex-1 break-all font-mono text-[0.8125rem] text-ink">
            {generatedKey}
          </code>
          <CopyButton value={generatedKey} label="Copy" />
        </div>
        <div className="flex justify-end">
          <Button onClick={() => router.push("/api-keys")}>Done</Button>
        </div>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-5" noValidate>
      <Input
        label="Key name"
        placeholder="Production billing service"
        hint="A name that tells you later which application this key belongs to."
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
      <div className="flex flex-col gap-2 border-t border-ink/12 pt-5 sm:flex-row sm:justify-end">
        <Button type="button" variant="secondary" onClick={() => router.back()}>
          Cancel
        </Button>
        <Button type="submit" loading={loading}>
          <Key className="h-4 w-4" aria-hidden />
          Generate key
        </Button>
      </div>
    </form>
  );
}
