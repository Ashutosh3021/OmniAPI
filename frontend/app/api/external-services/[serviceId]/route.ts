import { NextResponse } from "next/server";
import { getStore } from "@/lib/mockStore";
import { jsonError } from "@/lib/apiHelpers";
import { externalServiceSchema } from "@/lib/validators";
import { parseBody } from "@/lib/apiHelpers";

interface RouteParams {
  params: { serviceId: string };
}

export async function GET(_request: Request, { params }: RouteParams) {
  const { serviceId } = params;
  const svc = getStore().services.find((s) => s.id === serviceId);
  if (!svc) return jsonError("Service not found", 404);
  return NextResponse.json(svc);
}

export async function PUT(request: Request, { params }: RouteParams) {
  const { serviceId } = params;
  const parsed = await parseBody(request, externalServiceSchema);
  if ("error" in parsed) return parsed.error;

  const store = getStore();
  const index = store.services.findIndex((s) => s.id === serviceId);
  if (index === -1) return jsonError("Service not found", 404);

  store.services[index] = {
    ...store.services[index],
    name: parsed.data.name,
    serviceType: parsed.data.serviceType,
    rateLimit: parsed.data.rateLimit ?? null,
  };

  return NextResponse.json(store.services[index]);
}

export async function DELETE(_request: Request, { params }: RouteParams) {
  const { serviceId } = params;
  const store = getStore();
  const index = store.services.findIndex((s) => s.id === serviceId);
  if (index === -1) return jsonError("Service not found", 404);
  store.services.splice(index, 1);
  return new NextResponse(null, { status: 204 });
}
