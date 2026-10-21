import type { Metadata } from "next";
import { AuthCard } from "@/components/auth/AuthCard";
import { LoginForm } from "@/components/forms/LoginForm";

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
      subtitle="Use the email and password of your OmniAPI account."
    >
      <LoginForm />
    </AuthCard>
  );
}
