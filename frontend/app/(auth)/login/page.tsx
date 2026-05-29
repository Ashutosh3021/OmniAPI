import { AuthCard } from "@/components/auth/AuthCard";
import { LoginForm } from "@/components/forms/LoginForm";

export default function LoginPage() {
  return (
    <AuthCard title="OmniAPI" subtitle="Sign in to manage your infrastructure.">
      <LoginForm />
    </AuthCard>
  );
}
