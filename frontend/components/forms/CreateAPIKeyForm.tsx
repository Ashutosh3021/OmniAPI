"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Key } from "lucide-react";
import { Button } from "@/components/shared/Button";
import { Checkbox } from "@/components/shared/Checkbox";
import { Input } from "@/components/shared/Input";
import { API_KEY_PERMISSIONS } from "@/lib/constants";
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
    watch,
    setValue,
    formState: { errors },
  } = useForm<ApiKeyInput>({
    resolver: zodResolver(apiKeySchema),
    defaultValues: { permissions: ["read"] },
  });

  const permissions = watch("permissions") ?? [];

  const togglePermission = (id: string) => {
    const next = permissions.includes(id)
      ? permissions.filter((p) => p !== id)
      : [...permissions, id];
    setValue("permissions", next, { shouldValidate: true });
  };

  const onSubmit = async (data: ApiKeyInput) => {
    setLoading(true);
    try {
      const result = await api.post<ApiKey>("/api-keys", data);
      setGeneratedKey(result.key);
      notify("API key created successfully", "success");
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
        <code className="block p-md bg-slate-800 text-emerald-400 rounded font-mono text-code break-all">
          {generatedKey}
        </code>
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
      <div>
        <p className="text-label-md font-medium text-on-surface-variant mb-sm">Permissions</p>
        <div className="grid grid-cols-2 gap-sm">
          {API_KEY_PERMISSIONS.map((perm) => (
            <Checkbox
              key={perm.id}
              label={perm.label}
              checked={permissions.includes(perm.id)}
              onChange={() => togglePermission(perm.id)}
            />
          ))}
        </div>
        {errors.permissions && (
          <p className="text-body-sm text-error mt-sm" role="alert">
            {errors.permissions.message}
          </p>
        )}
      </div>
      <Input
        label="Expiration Date (Optional)"
        type="date"
        hint="If left blank, the key will never expire."
        error={errors.expirationDate?.message}
        {...register("expirationDate")}
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
