"use client";

import Link from "next/link";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Button } from "@/components/shared/Button";
import { Input } from "@/components/shared/Input";
import { useAuth } from "@/hooks/useAuth";
import { useNotification } from "@/context/NotificationContext";
import { loginSchema, type LoginInput } from "@/lib/validators";

export function LoginForm() {
  const { login } = useAuth();
  const { notify } = useNotification();
  const [loading, setLoading] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginInput>({
    resolver: zodResolver(loginSchema),
  });

  const onSubmit = async (data: LoginInput) => {
    setLoading(true);
    const ok = await login(data);
    setLoading(false);
    if (ok) {
      notify("Signed in", "success");
    } else {
      notify("That email and password did not match", "error");
    }
  };

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
      <Input
        label="Password"
        type="password"
        autoComplete="current-password"
        error={errors.password?.message}
        {...register("password")}
      />

      <div className="flex justify-end">
        <Link href="/forgot-password" className="link text-meta text-accent">
          Forgot password
        </Link>
      </div>

      <Button type="submit" fullWidth loading={loading}>
        Sign in
      </Button>

      <p className="text-center text-meta text-muted">
        No account yet?{" "}
        <Link href="/signup" className="link font-medium text-accent">
          Create one
        </Link>
      </p>
    </form>
  );
}
