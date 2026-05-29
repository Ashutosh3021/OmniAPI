import { NextResponse } from "next/server";
import { loginSchema } from "@/lib/validators";
import { parseBody, jsonError } from "@/lib/apiHelpers";
import { createMockToken } from "@/lib/jwt";
import { MOCK_USER } from "@/lib/mockData";

export async function POST(request: Request) {
  const parsed = await parseBody(request, loginSchema);
  if ("error" in parsed) return parsed.error;

  const { email, password } = parsed.data;

  if (email === "alex@example.com" && password === "password123") {
    const user = { ...MOCK_USER, email };
    const accessToken = createMockToken(user);
    const refreshToken = createMockToken(user, 86400 * 7);

    return NextResponse.json({
      user,
      tokens: {
        accessToken,
        refreshToken,
        expiresIn: 3600,
      },
    });
  }

  return jsonError("Invalid email or password", 401);
}
