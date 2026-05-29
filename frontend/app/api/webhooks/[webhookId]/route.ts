import { NextResponse } from "next/server";
import { getStore } from "@/lib/mockStore";
import { jsonError } from "@/lib/apiHelpers";
import { webhookSchema } from "@/lib/validators";
import { parseBody } from "@/lib/apiHelpers";

interface RouteParams {
  params: { webhookId: string };
}

export async function GET(_request: Request, { params }: RouteParams) {
  const { webhookId } = params;
  const wh = getStore().webhooks.find((w) => w.id === webhookId);
  if (!wh) return jsonError("Webhook not found", 404);
  return NextResponse.json(wh);
}

export async function PUT(request: Request, { params }: RouteParams) {
  const { webhookId } = params;
  const parsed = await parseBody(request, webhookSchema);
  if ("error" in parsed) return parsed.error;

  const store = getStore();
  const index = store.webhooks.findIndex((w) => w.id === webhookId);
  if (index === -1) return jsonError("Webhook not found", 404);

  store.webhooks[index] = {
    ...store.webhooks[index],
    name: parsed.data.name,
    url: parsed.data.url,
    events: parsed.data.events,
  };

  return NextResponse.json(store.webhooks[index]);
}

export async function DELETE(_request: Request, { params }: RouteParams) {
  const { webhookId } = params;
  const store = getStore();
  const index = store.webhooks.findIndex((w) => w.id === webhookId);
  if (index === -1) return jsonError("Webhook not found", 404);
  store.webhooks.splice(index, 1);
  return new NextResponse(null, { status: 204 });
}
