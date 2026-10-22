"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Pause, Play } from "lucide-react";
import { PageHeader } from "@/components/shared/PageHeader";
import { Badge } from "@/components/shared/Badge";
import { Button } from "@/components/shared/Button";
import { Spinner } from "@/components/shared/Spinner";
import { ConfirmDialog } from "@/components/shared/ConfirmDialog";
import { EmptyState } from "@/components/shared/EmptyState";
import { SERVICE_TYPES } from "@/lib/constants";
import { api } from "@/lib/api";
import { useNotification } from "@/context/NotificationContext";
import { formatDate } from "@/lib/utils";
import type { ExternalService } from "@/types";

export default function ExternalServiceDetailPage() {
  const { serviceId } = useParams<{ serviceId: string }>();
  const router = useRouter();
  const { notify } = useNotification();
  const [service, setService] = useState<ExternalService | null>(null);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let cancelled = false;
    api
      .get<ExternalService>(`/external-services/${serviceId}`)
      .then((data) => {
        if (!cancelled) setService(data);
      })
      .catch(() => {
        if (!cancelled) setNotFound(true);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [serviceId]);

  const setStatus = async (status: "active" | "inactive") => {
    setBusy(true);
    try {
      const updated = await api.patch<ExternalService>(
        `/external-services/${serviceId}`,
        { status }
      );
      setService(updated);
      notify(status === "active" ? "Service resumed" : "Service paused", "success");
    } catch {
      notify("Could not change the service status", "error");
    } finally {
      setBusy(false);
    }
  };

  const onDelete = async () => {
    setConfirmOpen(false);
    try {
      await api.delete(`/external-services/${serviceId}`);
      notify("Service removed", "success");
      router.push("/external-services");
    } catch {
      notify("Could not remove the service", "error");
    }
  };

  if (loading) return <Spinner full label="Loading service" />;

  if (notFound || !service) {
    return (
      <>
        <PageHeader title="Service not found" />
        <EmptyState
          title="This service does not exist."
          description="It may have been removed, or the link may be wrong."
        />
      </>
    );
  }

  const provider =
    SERVICE_TYPES.find((s) => s.value === service.service_name)?.label ??
    service.service_name;
  const active = service.status === "active";

  return (
    <div className="max-w-2xl">
      <PageHeader
        meta={`service ${service.service_id}`}
        title={service.service_name}
        description={provider}
        action={
          <Badge
            tone={active ? "ok" : service.status === "error" ? "bad" : "neutral"}
          >
            {service.status}
          </Badge>
        }
      />

      <div className="panel p-5 md:p-7">
        <dl className="space-y-2.5 text-ui">
          <div className="flex justify-between gap-4">
            <dt className="text-muted">Calls per hour</dt>
            <dd className="num text-ink">
              {service.max_calls_per_hour.toLocaleString()}
            </dd>
          </div>
          <div className="flex justify-between gap-4">
            <dt className="text-muted">Connected</dt>
            <dd className="text-ink">{formatDate(service.created_at)}</dd>
          </div>
          <div className="flex justify-between gap-4">
            <dt className="text-muted">Provider key</dt>
            <dd className="text-muted">encrypted, never returned</dd>
          </div>
        </dl>

        <div className="mt-6 flex flex-col gap-2 border-t border-ink/12 pt-5 sm:flex-row sm:justify-between">
          <Button variant="danger" onClick={() => setConfirmOpen(true)}>
            Disconnect
          </Button>
          <Button
            variant="secondary"
            loading={busy}
            onClick={() => setStatus(active ? "inactive" : "active")}
          >
            {active ? (
              <>
                <Pause className="h-4 w-4" aria-hidden />
                Pause service
              </>
            ) : (
              <>
                <Play className="h-4 w-4" aria-hidden />
                Resume service
              </>
            )}
          </Button>
        </div>
      </div>

      <ConfirmDialog
        open={confirmOpen}
        title="Disconnect this service?"
        description={`The ${service.service_name} provider key is deleted and the branch stops answering. You can connect it again later.`}
        confirmLabel="Disconnect"
        onClose={() => setConfirmOpen(false)}
        onConfirm={onDelete}
      />
    </div>
  );
}
