import { NextResponse } from "next/server";
import type { ZodSchema } from "zod";

export function jsonError(message: string, status: number) {
  return NextResponse.json({ error: message }, { status });
}

export async function parseBody<T>(
  request: Request,
  schema: ZodSchema<T>
): Promise<{ data: T } | { error: NextResponse }> {
  try {
    const body: unknown = await request.json();
    const result = schema.safeParse(body);
    if (!result.success) {
      return {
        error: NextResponse.json(
          { error: result.error.issues[0]?.message ?? "Validation failed" },
          { status: 400 }
        ),
      };
    }
    return { data: result.data };
  } catch {
    return { error: jsonError("Invalid JSON body", 400) };
  }
}
