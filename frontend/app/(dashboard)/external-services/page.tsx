"use client";

import Link from "next/link";
import { useEffect, useState, useCallback } from "react";
import { Plus } from "lucide-react";
import { ExternalServicesTable } from "@/components/tables/ExternalServicesTable";
import { PageHeader } from "@/components/shared/PageHeader";
import { Button } from "@/components/shared/Button";
import { Spinner } from "@/components/shared/Spinner";
import { Card } from "@/components/shared/Card";
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
      notify("Failed to load services", "error");
    }
    setLoading(false);
  }, [notify]);

  useEffect(() => {
    load();
  }, [load]);

  const handleDelete = async (id: string) => {
    try {
      await api.delete(`/external-services/${id}`);
      notify("Service removed", "success");
      load();
    } catch {
      notify("Failed to delete service", "error");
    }
  };

  return (
    <>
      <PageHeader
        title="External Services"
        description="Connect and manage third-party integrations"
        action={
          <Link href="/external-services/create">
            <Button>
              <Plus className="h-4 w-4" />
              Add Service
            </Button>
          </Link>
        }
      />
      <Card padding="sm">
        {loading ? (
          <Spinner />
        ) : (
          <ExternalServicesTable services={services} onDelete={handleDelete} />
        )}
      </Card>
    </>
  );
}
