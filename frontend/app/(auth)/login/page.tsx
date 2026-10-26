import type { Metadata } from "next";
import { AuthCard } from "@/components/auth/AuthCard";
import { SignInOptions } from "@/components/auth/SignInOptions";

export const metadata: Metadata = {
  title: "Sign in",
  description:
    "Sign in to manage your OmniAPI keys, providers, webhooks and usage.",
  robots: { index: false, follow: true },
};

export default function LoginPage() {
  return (
    <AuthCard
      title="Sign in"
      subtitle="One account, one gateway. Continue with the provider you already use."
    >
      <SignInOptions />
    </AuthCard>
  );
}
