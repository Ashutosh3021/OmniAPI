"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Plug } from "lucide-react";
import { Button } from "@/components/shared/Button";
import { Input } from "@/components/shared/Input";
import { Select } from "@/components/shared/Select";
import { SERVICE_TYPES } from "@/lib/constants";
import { api } from "@/lib/api";
import { useNotification } from "@/context/NotificationContext";
import {
  externalServiceSchema,
  type ExternalServiceInput,
} from "@/lib/validators";
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
    defaultValues: { max_calls_per_hour: 100 },
  });

  const onSubmit = async (data: ExternalServiceInput) => {
    setLoading(true);
    try {
      await api.post<ExternalService>("/external-services", {
        service_name: data.service_name,
        api_key: data.api_key,
        max_calls_per_hour: data.max_calls_per_hour ?? 100,
      });
      notify("Service connected", "success");
      router.push("/external-services");
    } catch {
      notify("Could not connect that service", "error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-5" noValidate>
      <Select
        label="Provider"
        placeholder="Choose a provider"
        options={SERVICE_TYPES.map((s) => ({ value: s.value, label: s.label }))}
        hint="The gateway ships with three providers. Each one becomes a branch you can call."
        error={errors.service_name?.message}
        {...register("service_name")}
      />
      <Input
        label="Provider API key"
        type="password"
        placeholder="your provider key"
        hint="Encrypted at rest with AES-256. It is never returned by the API."
        error={errors.api_key?.message}
        {...register("api_key")}
      />
      <Input
        label="Calls per hour"
        type="number"
        min={1}
        max={100000}
        hint="The ceiling OmniAPI will hold this provider to."
        error={errors.max_calls_per_hour?.message}
        {...register("max_calls_per_hour", { valueAsNumber: true })}
      />
      <div className="flex flex-col gap-2 border-t border-ink/12 pt-5 sm:flex-row sm:justify-end">
        <Button type="button" variant="secondary" onClick={() => router.back()}>
          Cancel
        </Button>
        <Button type="submit" loading={loading}>
          <Plug className="h-4 w-4" aria-hidden />
          Connect provider
        </Button>
      </div>
    </form>
  );
}
