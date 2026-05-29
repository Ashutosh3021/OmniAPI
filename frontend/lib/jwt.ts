import type { User } from "@/types";

function base64UrlEncode(str: string): string {
  return Buffer.from(str)
    .toString("base64")
    .replace(/\+/g, "-")
    .replace(/\//g, "_")
    .replace(/=+$/, "");
}

export function createMockToken(user: User, expiresInSeconds = 3600): string {
  const header = base64UrlEncode(JSON.stringify({ alg: "HS256", typ: "JWT" }));
  const payload = base64UrlEncode(
    JSON.stringify({
      sub: user.id,
      email: user.email,
      name: user.name,
      exp: Math.floor(Date.now() / 1000) + expiresInSeconds,
    })
  );
  const signature = base64UrlEncode("mock-signature");
  return `${header}.${payload}.${signature}`;
}
