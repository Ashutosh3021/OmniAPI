import { NextResponse } from "next/server";
import { webhookSchema } from "@/lib/validators";
import { parseBody } from "@/lib/apiHelpers";
import { getStore, createWebhookRecord } from "@/lib/mockStore";

export async function GET() {
  return NextResponse.json(getStore().webhooks);
}

export async function POST(request: Request) {
  const parsed = await parseBody(request, webhookSchema);
  if ("error" in parsed) return parsed.error;

  const record = createWebhookRecord({
    name: parsed.data.name,
    url: parsed.data.url,
    events: parsed.data.events,
  });

  return NextResponse.json(record, { status: 201 });
}
