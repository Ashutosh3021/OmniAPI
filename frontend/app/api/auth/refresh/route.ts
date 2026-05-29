import { NextResponse } from "next/server";
import { createMockToken } from "@/lib/jwt";
import { MOCK_USER } from "@/lib/mockData";

export async function POST() {
  const user = MOCK_USER;
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
