import { NextResponse } from "next/server";
import { externalServiceSchema } from "@/lib/validators";
import { parseBody } from "@/lib/apiHelpers";
import { getStore, createServiceRecord } from "@/lib/mockStore";

export async function GET() {
  return NextResponse.json(getStore().services);
}

export async function POST(request: Request) {
  const parsed = await parseBody(request, externalServiceSchema);
  if ("error" in parsed) return parsed.error;

  const record = createServiceRecord({
    name: parsed.data.name,
    serviceType: parsed.data.serviceType,
    rateLimit: parsed.data.rateLimit ?? null,
  });

  return NextResponse.json(record, { status: 201 });
}
