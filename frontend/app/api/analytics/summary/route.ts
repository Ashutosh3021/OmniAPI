import { NextResponse } from "next/server";
import { getStore } from "@/lib/mockStore";

export async function GET() {
  return NextResponse.json(getStore().analytics);
}
