import { AuthCard } from "@/components/auth/AuthCard";
import { ForgotPasswordForm } from "@/components/forms/ForgotPasswordForm";

export default function ForgotPasswordPage() {
  return (
    <AuthCard title="Reset Password" subtitle="Enter your email to receive a reset link.">
      <ForgotPasswordForm />
    </AuthCard>
  );
}
