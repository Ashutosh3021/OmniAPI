import { NextResponse } from "next/server";
import { apiKeySchema } from "@/lib/validators";
import { parseBody } from "@/lib/apiHelpers";
import { getStore, createApiKeyRecord } from "@/lib/mockStore";

export async function GET() {
  const store = getStore();
  const keys = store.apiKeys.map((k) => ({
    ...k,
    key: `${k.keyPrefix}_sk_****${k.key.slice(-4)}`,
  }));
  return NextResponse.json(keys);
}

export async function POST(request: Request) {
  const parsed = await parseBody(request, apiKeySchema);
  if ("error" in parsed) return parsed.error;

  const record = createApiKeyRecord({
    name: parsed.data.name,
    permissions: parsed.data.permissions,
    expiresAt: parsed.data.expirationDate || null,
  });

  return NextResponse.json(record, { status: 201 });
}
