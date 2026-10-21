"use client";

import { useEffect, useState, useCallback } from "react";
import { Plus } from "lucide-react";
import { ExternalServicesTable } from "@/components/tables/ExternalServicesTable";
import { PageHeader } from "@/components/shared/PageHeader";
import { ButtonLink } from "@/components/shared/Button";
import { Spinner } from "@/components/shared/Spinner";
import { api } from "@/lib/api";
import { useNotification } from "@/context/NotificationContext";
import type { ExternalService } from "@/types";

export default function ExternalServicesPage() {
  const [services, setServices] = useState<ExternalService[]>([]);
  const [loading, setLoading] = useState(true);
  const { notify } = useNotification();

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setServices(await api.get<ExternalService[]>("/external-services"));
    } catch {
      notify("Could not load your services", "error");
    } finally {
      setLoading(false);
    }
  }, [notify]);

  useEffect(() => {
    load();
  }, [load]);

  const handleDelete = async (id: number) => {
    try {
      await api.delete(`/external-services/${id}`);
      notify("Service removed", "success");
      load();
    } catch {
      notify("Could not remove that service", "error");
    }
  };

  return (
    <>
      <PageHeader
        meta={loading ? undefined : `${services.length} connected`}
        title="External services"
        description="The third-party APIs OmniAPI can call for you. Each provider key is encrypted at rest and never appears in a response."
        action={
          <ButtonLink href="/external-services/create" size="sm">
            <Plus className="h-4 w-4" aria-hidden />
            Add service
          </ButtonLink>
        }
      />

      {loading ? (
        <Spinner label="Loading services" />
      ) : (
        <ExternalServicesTable services={services} onDelete={handleDelete} />
      )}
    </>
  );
}
