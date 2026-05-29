"use client";

import Link from "next/link";
import { Trash2 } from "lucide-react";
import { Badge } from "@/components/shared/Badge";
import { SERVICE_TYPES } from "@/lib/constants";
import { formatRelativeTime } from "@/lib/utils";
import type { ExternalService } from "@/types";

interface ExternalServicesTableProps {
  services: ExternalService[];
  onDelete?: (id: string) => void;
}

export function ExternalServicesTable({ services, onDelete }: ExternalServicesTableProps) {
  const getLabel = (type: string) =>
    SERVICE_TYPES.find((s) => s.value === type)?.label ?? type;

  if (services.length === 0) {
    return (
      <p className="text-body-md text-on-surface-variant py-xl text-center">
        No external services connected.
      </p>
    );
  }

  return (
    <>
      <div className="hidden md:block overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-surface-container-low border-b border-outline">
              <th className="py-sm px-lg text-label-sm text-on-surface-variant uppercase font-semibold">Name</th>
              <th className="py-sm px-lg text-label-sm text-on-surface-variant uppercase font-semibold">Provider</th>
              <th className="py-sm px-lg text-label-sm text-on-surface-variant uppercase font-semibold">Status</th>
              <th className="py-sm px-lg text-label-sm text-on-surface-variant uppercase font-semibold">Rate Limit</th>
              <th className="py-sm px-lg text-label-sm text-on-surface-variant uppercase font-semibold">Last Sync</th>
              <th className="py-sm px-lg text-label-sm text-on-surface-variant uppercase font-semibold">Actions</th>
            </tr>
          </thead>
          <tbody>
            {services.map((svc) => (
              <tr key={svc.id} className="border-b border-outline-variant hover:bg-surface-container-low">
                <td className="py-md px-lg">
                  <Link href={`/external-services/${svc.id}`} className="text-secondary-fixed hover:underline font-medium">
                    {svc.name}
                  </Link>
                </td>
                <td className="py-md px-lg text-body-sm">{getLabel(svc.serviceType)}</td>
                <td className="py-md px-lg">
                  <Badge variant={svc.status === "connected" ? "success" : "error"}>{svc.status}</Badge>
                </td>
                <td className="py-md px-lg text-body-sm">{svc.rateLimit ?? "Unlimited"}</td>
                <td className="py-md px-lg text-body-sm text-on-surface-variant">
                  {formatRelativeTime(svc.lastSync)}
                </td>
                <td className="py-md px-lg">
                  {onDelete && (
                    <button type="button" onClick={() => onDelete(svc.id)} className="p-1 hover:text-error" aria-label={`Delete ${svc.name}`}>
                      <Trash2 className="h-4 w-4" />
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="md:hidden space-y-md">
        {services.map((svc) => (
          <Link key={svc.id} href={`/external-services/${svc.id}`} className="block border border-outline rounded-xl p-md bg-white dark:bg-surface">
            <div className="flex justify-between mb-sm">
              <span className="font-medium">{svc.name}</span>
              <Badge variant={svc.status === "connected" ? "success" : "error"}>{svc.status}</Badge>
            </div>
            <p className="text-body-sm text-on-surface-variant">{getLabel(svc.serviceType)}</p>
          </Link>
        ))}
      </div>
    </>
  );
}
