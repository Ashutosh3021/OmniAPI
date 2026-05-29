import { NextResponse } from "next/server";
import { getStore } from "@/lib/mockStore";
import { jsonError } from "@/lib/apiHelpers";
import { apiKeySchema } from "@/lib/validators";
import { parseBody } from "@/lib/apiHelpers";

interface RouteParams {
  params: { keyId: string };
}

export async function GET(_request: Request, { params }: RouteParams) {
  const { keyId } = params;
  const store = getStore();
  const key = store.apiKeys.find((k) => k.id === keyId);
  if (!key) return jsonError("API key not found", 404);
  return NextResponse.json(key);
}

export async function PUT(request: Request, { params }: RouteParams) {
  const { keyId } = params;
  const parsed = await parseBody(request, apiKeySchema);
  if ("error" in parsed) return parsed.error;

  const store = getStore();
  const index = store.apiKeys.findIndex((k) => k.id === keyId);
  if (index === -1) return jsonError("API key not found", 404);

  store.apiKeys[index] = {
    ...store.apiKeys[index],
    name: parsed.data.name,
    permissions: parsed.data.permissions,
    expiresAt: parsed.data.expirationDate || null,
  };

  return NextResponse.json(store.apiKeys[index]);
}

export async function DELETE(_request: Request, { params }: RouteParams) {
  const { keyId } = params;
  const store = getStore();
  const index = store.apiKeys.findIndex((k) => k.id === keyId);
  if (index === -1) return jsonError("API key not found", 404);
  store.apiKeys.splice(index, 1);
  return new NextResponse(null, { status: 204 });
}
