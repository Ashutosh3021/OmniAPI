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
      // Backend accepts { name, expires_at } and returns { ..., raw_key }
      const payload: { name: string; expires_at?: string } = { name: data.name };
      if (data.expires_at) {
        // Convert date string (YYYY-MM-DD) to ISO-8601 datetime expected by the backend
        payload.expires_at = new Date(data.expires_at).toISOString();
      }

      const result = await api.post<ApiKey & { raw_key: string }>("/api-keys", payload);
      if (result.raw_key) {
        setGeneratedKey(result.raw_key);
        notify("API key created successfully", "success");
      } else {
        notify("Key created but secret was not returned — contact support", "error");
      }
    } catch {
      notify("Failed to create API key", "error");
    }
    setLoading(false);
  };

  if (generatedKey) {
    return (
      <div className="space-y-md">
        <p className="text-body-md text-on-surface-variant">
          Copy this key now. You won&apos;t be able to see it again.
        </p>
        <div className="relative flex items-start gap-2 p-md bg-slate-800 rounded">
          <code className="flex-1 text-emerald-400 font-mono text-code break-all">
            {generatedKey}
          </code>
          <CopyButton value={generatedKey} label="Copy API key to clipboard" />
        </div>
        <div className="flex gap-md justify-end">
          <Button variant="secondary" onClick={() => router.push("/api-keys")}>
            Done
          </Button>
        </div>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-xl" noValidate>
      <Input
        label="Key Name"
        placeholder="e.g. Production Billing Service"
        hint="A descriptive name to identify this key later."
        error={errors.name?.message}
        {...register("name")}
      />
      <Input
        label="Expiration Date (Optional)"
        type="date"
        hint="If left blank, the key will never expire."
        error={errors.expires_at?.message}
        {...register("expires_at")}
      />
      <div className="flex flex-col sm:flex-row justify-end gap-md pt-lg border-t border-outline-variant">
        <Button type="button" variant="secondary" onClick={() => router.back()}>
          Cancel
        </Button>
        <Button type="submit" loading={loading}>
          <Key className="h-4 w-4" />
          Generate Key
        </Button>
      </div>
    </form>
  );
}
