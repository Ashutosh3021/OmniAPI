"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { PageHeader } from "@/components/shared/PageHeader";
import { Card } from "@/components/shared/Card";
import { Badge } from "@/components/shared/Badge";
import { Button } from "@/components/shared/Button";
import { Spinner } from "@/components/shared/Spinner";
import { SERVICE_TYPES } from "@/lib/constants";
import { api } from "@/lib/api";
import { useNotification } from "@/context/NotificationContext";
import { formatDate, formatRelativeTime } from "@/lib/utils";
import type { ExternalService } from "@/types";

export default function ExternalServiceDetailPage() {
  const { serviceId } = useParams<{ serviceId: string }>();
  const router = useRouter();
  const { notify } = useNotification();
  const [service, setService] = useState<ExternalService | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get<ExternalService>(`/external-services/${serviceId}`)
      .then(setService)
      .finally(() => setLoading(false));
  }, [serviceId]);

  const onDelete = async () => {
    try {
      await api.delete(`/external-services/${serviceId}`);
      notify("Service removed", "success");
      router.push("/external-services");
    } catch {
      notify("Failed to remove service", "error");
    }
  };

  if (loading) return <Spinner />;
  if (!service) return <p>Service not found</p>;

  const provider =
    SERVICE_TYPES.find((s) => s.value === service.serviceType)?.label ??
    service.serviceType;

  return (
    <div className="max-w-2xl mx-auto">
      <PageHeader title={service.name} description={provider} />
      <Card>
        <dl className="space-y-md text-body-md">
          <div className="flex justify-between">
            <dt className="text-on-surface-variant">Status</dt>
            <dd>
              <Badge variant={service.status === "connected" ? "success" : "error"}>
                {service.status}
              </Badge>
            </dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-on-surface-variant">Rate limit</dt>
            <dd>{service.rateLimit ?? "Unlimited"} / hour</dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-on-surface-variant">Created</dt>
            <dd>{formatDate(service.createdAt)}</dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-on-surface-variant">Last sync</dt>
            <dd>{formatRelativeTime(service.lastSync)}</dd>
          </div>
        </dl>
        <div className="mt-lg pt-lg border-t border-outline-variant flex gap-md">
          <Button variant="secondary" onClick={() => router.push("/external-services/create")}>
            Reconfigure
          </Button>
          <Button variant="danger" onClick={onDelete}>
            Disconnect
          </Button>
        </div>
      </Card>
    </div>
  );
}
