"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Save } from "lucide-react";
import { Button } from "@/components/shared/Button";
import { Input } from "@/components/shared/Input";
import { Select } from "@/components/shared/Select";
import { SERVICE_TYPES } from "@/lib/constants";
import { api } from "@/lib/api";
import { useNotification } from "@/context/NotificationContext";
import { externalServiceSchema, type ExternalServiceInput } from "@/lib/validators";
import type { ExternalService } from "@/types";

export function CreateExternalServiceForm() {
  const router = useRouter();
  const { notify } = useNotification();
  const [loading, setLoading] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ExternalServiceInput>({
    resolver: zodResolver(externalServiceSchema),
  });

  const onSubmit = async (data: ExternalServiceInput) => {
    setLoading(true);
    try {
      await api.post<ExternalService>("/external-services", data);
      notify("External service added successfully", "success");
      router.push("/external-services");
    } catch {
      notify("Failed to add service", "error");
    }
    setLoading(false);
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-xl" noValidate>
      <Input
        label="Service Name"
        placeholder="e.g. Stripe Payments"
        error={errors.name?.message}
        {...register("name")}
      />
      <Select
        label="Service Type"
        placeholder="Select a provider..."
        options={SERVICE_TYPES.map((s) => ({ value: s.value, label: s.label }))}
        error={errors.serviceType?.message}
        hint="Select the platform you wish to integrate."
        {...register("serviceType")}
      />
      <Input
        label="API Key / Bearer Token"
        type="password"
        placeholder="sk_test_..."
        hint="Stored securely using AES-256 encryption."
        error={errors.apiKey?.message}
        {...register("apiKey")}
      />
      <Input
        label="Rate Limit (calls/hour)"
        type="number"
        placeholder="1000"
        hint="Optional. Leave blank for unlimited based on plan."
        className="md:max-w-xs"
        {...register("rateLimit", { valueAsNumber: true })}
      />
      <div className="flex flex-col sm:flex-row justify-end gap-md pt-lg border-t border-outline-variant/30">
        <Button type="button" variant="secondary" onClick={() => router.back()}>
          Cancel
        </Button>
        <Button type="submit" loading={loading}>
          <Save className="h-4 w-4" />
          Save Service
        </Button>
      </div>
    </form>
  );
}
