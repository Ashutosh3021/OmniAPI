"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Button } from "@/components/shared/Button";
import { Input } from "@/components/shared/Input";
import { useNotification } from "@/context/NotificationContext";
import { useAuth } from "@/hooks/useAuth";
import { profileSchema } from "@/lib/validators";
import { z } from "zod";

type ProfileInput = z.infer<typeof profileSchema>;

export function ProfileForm() {
  const { user } = useAuth();
  const { notify } = useNotification();
  const [loading, setLoading] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ProfileInput>({
    resolver: zodResolver(profileSchema),
    defaultValues: {
      name: user?.name ?? "",
      email: user?.email ?? "",
      company: user?.company ?? "",
    },
  });

  const onSubmit = async () => {
    setLoading(true);
    await new Promise((r) => setTimeout(r, 500));
    setLoading(false);
    notify("Profile updated", "success");
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-lg max-w-lg">
      <Input label="Full Name" error={errors.name?.message} {...register("name")} />
      <Input label="Email" type="email" error={errors.email?.message} {...register("email")} />
      <Input label="Company" error={errors.company?.message} {...register("company")} />
      <Button type="submit" loading={loading}>
        Save Changes
      </Button>
    </form>
  );
}
