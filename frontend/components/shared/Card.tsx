import { cn } from "@/lib/utils";

interface CardProps {
  children: React.ReactNode;
  className?: string;
  padding?: "sm" | "md" | "lg";
}

export function Card({ children, className, padding = "lg" }: CardProps) {
  const paddingClass = {
    sm: "p-md",
    md: "p-lg",
    lg: "p-lg md:p-xl",
  }[padding];

  return (
    <div
      className={cn(
        "bg-white dark:bg-surface border border-outline rounded-xl shadow-sm",
        paddingClass,
        className
      )}
    >
      {children}
    </div>
  );
}
