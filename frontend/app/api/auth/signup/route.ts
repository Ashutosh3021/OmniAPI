import { NextResponse } from "next/server";
import { z } from "zod";
import { parseBody } from "@/lib/apiHelpers";
import { createMockToken } from "@/lib/jwt";
import { generateId } from "@/lib/utils";

const signupBodySchema = z.object({
  name: z.string().min(2),
  email: z.string().email(),
  password: z.string().min(8),
});

export async function POST(request: Request) {
  const parsed = await parseBody(request, signupBodySchema);
  if ("error" in parsed) return parsed.error;

  const user = {
    id: generateId("user"),
    name: parsed.data.name,
    email: parsed.data.email,
    company: "",
  };

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
