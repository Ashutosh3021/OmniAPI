"use client";

import Link from "next/link";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Mail, Lock, User } from "lucide-react";
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
    const ok = await signup(data);
    setLoading(false);
    if (ok) {
      notify("Account created successfully!", "success");
    } else {
      notify("Could not create account", "error");
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-lg" noValidate>
      <Input
        label="Full Name"
        leftIcon={<User className="h-5 w-5" />}
        error={errors.name?.message}
        {...register("name")}
      />
      <Input
        label="Email Address"
        type="email"
        leftIcon={<Mail className="h-5 w-5" />}
        error={errors.email?.message}
        {...register("email")}
      />
      <Input
        label="Password"
        type="password"
        leftIcon={<Lock className="h-5 w-5" />}
        error={errors.password?.message}
        {...register("password")}
      />
      <Input
        label="Confirm Password"
        type="password"
        leftIcon={<Lock className="h-5 w-5" />}
        error={errors.confirmPassword?.message}
        {...register("confirmPassword")}
      />
      <Button type="submit" fullWidth loading={loading}>
        Create Account
      </Button>
      <p className="text-center text-body-sm text-on-surface-variant">
        Already have an account?{" "}
        <Link href="/login" className="text-secondary-fixed font-medium hover:underline">
          Sign in
        </Link>
      </p>
    </form>
  );
}
