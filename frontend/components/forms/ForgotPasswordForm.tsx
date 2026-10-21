"use client";

import Link from "next/link";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Button } from "@/components/shared/Button";
import { Input } from "@/components/shared/Input";
import { forgotPasswordSchema, type ForgotPasswordInput } from "@/lib/validators";

export function ForgotPasswordForm() {
  const [submitted, setSubmitted] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ForgotPasswordInput>({
    resolver: zodResolver(forgotPasswordSchema),
  });

  const onSubmit = () => {
    setSubmitted(true);
  };

  if (submitted) {
    return (
      <div className="flex flex-col gap-4">
        <div className="rounded border border-warn/40 bg-warn/10 p-4">
          <p className="label-wire mb-1.5 text-warn">not available</p>
          <p className="text-ui text-ink">
            This deployment does not expose a password reset endpoint, so no
            email was sent. Ask the account owner to reset it, or create a new
            API key from the dashboard.
          </p>
        </div>
        <Button variant="secondary" fullWidth onClick={() => setSubmitted(false)}>
          Back
        </Button>
        <p className="text-center text-meta text-muted">
          <Link href="/login" className="link font-medium text-accent">
            Back to sign in
          </Link>
        </p>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4" noValidate>
      <Input
        label="Email"
        type="email"
        autoComplete="email"
        placeholder="you@company.com"
        error={errors.email?.message}
        {...register("email")}
      />

      <Button type="submit" fullWidth>
        Send reset link
      </Button>

      <p className="text-center text-meta text-muted">
        <Link href="/login" className="link font-medium text-accent">
          Back to sign in
        </Link>
      </p>
    </form>
  );
}
