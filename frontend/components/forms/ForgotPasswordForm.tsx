"use client";

import Link from "next/link";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Mail } from "lucide-react";
import { Button } from "@/components/shared/Button";
import { Input } from "@/components/shared/Input";
import { useNotification } from "@/context/NotificationContext";
import { forgotPasswordSchema, type ForgotPasswordInput } from "@/lib/validators";

export function ForgotPasswordForm() {
  const { notify } = useNotification();
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ForgotPasswordInput>({
    resolver: zodResolver(forgotPasswordSchema),
  });

  const onSubmit = async () => {
    setLoading(true);
    await new Promise((r) => setTimeout(r, 800));
    setLoading(false);
    setSent(true);
    notify("Password reset link sent to your email", "success");
  };

  if (sent) {
    return (
      <div className="text-center space-y-md">
        <p className="text-body-md text-on-surface-variant">
          Check your inbox for a password reset link.
        </p>
        <Link href="/login" className="text-secondary-fixed font-medium hover:underline">
          Back to sign in
        </Link>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-lg" noValidate>
      <Input
        label="Email Address"
        type="email"
        leftIcon={<Mail className="h-5 w-5" />}
        error={errors.email?.message}
        hint="We'll send you a link to reset your password."
        {...register("email")}
      />
      <Button type="submit" fullWidth loading={loading}>
        Send Reset Link
      </Button>
      <p className="text-center text-body-sm">
        <Link href="/login" className="text-secondary-fixed hover:underline">
          Back to sign in
        </Link>
      </p>
    </form>
  );
}
