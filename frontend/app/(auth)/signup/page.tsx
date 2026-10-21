import type { Metadata } from "next";
import { AuthCard } from "@/components/auth/AuthCard";
import { SignupForm } from "@/components/forms/SignupForm";

export const metadata: Metadata = {
  title: "Create an account",
  description:
    "Create an OmniAPI account, connect your providers and call them all through one endpoint.",
  robots: { index: false, follow: true },
};

export default function SignupPage() {
  return (
    <AuthCard
      title="Create an account"
      subtitle="Start with one provider. Add the rest whenever you need them."
    >
      <SignupForm />
    </AuthCard>
  );
}
