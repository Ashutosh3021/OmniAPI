"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Button } from "@/components/shared/Button";
import { Input } from "@/components/shared/Input";
import { useNotification } from "@/context/NotificationContext";
import { securitySchema } from "@/lib/validators";
import { z } from "zod";

type SecurityInput = z.infer<typeof securitySchema>;

export function SecuritySettings() {
  const { notify } = useNotification();
  const [loading, setLoading] = useState(false);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<SecurityInput>({
    resolver: zodResolver(securitySchema),
  });

  const onSubmit = async () => {
    setLoading(true);
    await new Promise((r) => setTimeout(r, 500));
    setLoading(false);
    reset();
    notify("Password updated successfully", "success");
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-lg max-w-lg">
      <Input
        label="Current Password"
        type="password"
        error={errors.currentPassword?.message}
        {...register("currentPassword")}
      />
      <Input
        label="New Password"
        type="password"
        error={errors.newPassword?.message}
        {...register("newPassword")}
      />
      <Input
        label="Confirm New Password"
        type="password"
        error={errors.confirmPassword?.message}
        {...register("confirmPassword")}
      />
      <Button type="submit" loading={loading}>
        Update Password
      </Button>
    </form>
  );
}
