"use client";

import Link from "next/link";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Mail, Lock } from "lucide-react";
import { Button } from "@/components/shared/Button";
import { Input } from "@/components/shared/Input";
import { useAuth } from "@/hooks/useAuth";
import { useNotification } from "@/context/NotificationContext";
import { loginSchema, type LoginInput } from "@/lib/validators";
import { useState } from "react";

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
      notify("Welcome back!", "success");
    } else {
      notify("Invalid email or password", "error");
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-lg" noValidate>
      <Input
        label="Email Address"
        type="email"
        autoComplete="email"
        leftIcon={<Mail className="h-5 w-5" />}
        error={errors.email?.message}
        {...register("email")}
      />
      <Input
        label="Password"
        type="password"
        autoComplete="current-password"
        leftIcon={<Lock className="h-5 w-5" />}
        error={errors.password?.message}
        {...register("password")}
      />
      <div className="flex justify-end">
        <Link
          href="/forgot-password"
          className="text-body-sm text-secondary-fixed hover:underline"
        >
          Forgot password?
        </Link>
      </div>
      <Button type="submit" fullWidth loading={loading}>
        Sign In
      </Button>
      <p className="text-center text-body-sm text-on-surface-variant">
        Don&apos;t have an account?{" "}
        <Link href="/signup" className="text-secondary-fixed font-medium hover:underline">
          Sign up
        </Link>
      </p>
    </form>
  );
}
