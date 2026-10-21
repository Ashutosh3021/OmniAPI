interface AuthCardProps {
  title: string;
  subtitle: string;
  children: React.ReactNode;
}

export function AuthCard({ title, subtitle, children }: AuthCardProps) {
  return (
    <div className="w-full">
      <div className="mb-7">
        <h1 className="t-title text-ink">{title}</h1>
        <p className="mt-2 text-ui text-muted">{subtitle}</p>
      </div>
      {children}
    </div>
  );
}
