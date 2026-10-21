"use client";

import Link from "next/link";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Button } from "@/components/shared/Button";
import { Input } from "@/components/shared/Input";
import { useAuth } from "@/hooks/useAuth";
import { useNotification } from "@/context/NotificationContext";
import { signupSchema, type SignupInput } from "@/lib/validators";

export function SignupForm() {
  const { signup } = useAuth();
  const { notify } = useNotification();
  const [loading, setLoading] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<SignupInput>({
    resolver: zodResolver(signupSchema),
  });

  const onSubmit = async (data: SignupInput) => {
    setLoading(true);
    const ok = await signup({
      name: data.name,
      email: data.email,
      password: data.password,
    });
    setLoading(false);
    if (ok) {
      notify("Account created", "success");
    } else {
      notify("That account could not be created", "error");
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4" noValidate>
      <Input
        label="Name"
        autoComplete="name"
        placeholder="Ada Lovelace"
        error={errors.name?.message}
        {...register("name")}
      />
      <Input
        label="Email"
        type="email"
        autoComplete="email"
        placeholder="you@company.com"
        error={errors.email?.message}
        {...register("email")}
      />
      <Input
        label="Password"
        type="password"
        autoComplete="new-password"
        hint="At least 8 characters."
        error={errors.password?.message}
        {...register("password")}
      />
      <Input
        label="Confirm password"
        type="password"
        autoComplete="new-password"
        error={errors.confirmPassword?.message}
        {...register("confirmPassword")}
      />

      <Button type="submit" fullWidth loading={loading}>
        Create account
      </Button>

      <p className="text-center text-meta text-muted">
        Already have an account?{" "}
        <Link href="/login" className="link font-medium text-accent">
          Sign in
        </Link>
      </p>
    </form>
  );
}
