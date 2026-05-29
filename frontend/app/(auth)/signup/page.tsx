import { AuthCard } from "@/components/auth/AuthCard";
import { SignupForm } from "@/components/forms/SignupForm";

export default function SignupPage() {
  return (
    <AuthCard title="OmniAPI" subtitle="Create your account to get started.">
      <SignupForm />
    </AuthCard>
  );
}
