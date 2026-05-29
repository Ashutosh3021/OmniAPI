import { NextResponse } from "next/server";
import {
  MOCK_ANALYTICS_SUMMARY,
  MOCK_USAGE_DATA,
  MOCK_CACHE_DATA,
  MOCK_LATENCY_DATA,
  MOCK_ENDPOINT_DATA,
} from "@/lib/mockData";
import { getStore } from "@/lib/mockStore";

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const type = searchParams.get("type");

  if (type === "summary") {
    return NextResponse.json(getStore().analytics);
  }
  if (type === "usage") {
    return NextResponse.json(MOCK_USAGE_DATA);
  }
  if (type === "cache") {
    return NextResponse.json(MOCK_CACHE_DATA);
  }
  if (type === "latency") {
    return NextResponse.json(MOCK_LATENCY_DATA);
  }
  if (type === "endpoints") {
    return NextResponse.json(MOCK_ENDPOINT_DATA);
  }

  return NextResponse.json({
    summary: getStore().analytics ?? MOCK_ANALYTICS_SUMMARY,
    usage: MOCK_USAGE_DATA,
    cache: MOCK_CACHE_DATA,
    latency: MOCK_LATENCY_DATA,
    endpoints: MOCK_ENDPOINT_DATA,
  });
}
