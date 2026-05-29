import { NextResponse } from "next/server";
import { MOCK_USAGE_DATA } from "@/lib/mockData";
import { getStore } from "@/lib/mockStore";

export async function GET() {
  return NextResponse.json({
    summary: getStore().analytics,
    usage: MOCK_USAGE_DATA,
    activity: getStore().activity,
  });
}
