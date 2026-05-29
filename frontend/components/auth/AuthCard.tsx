interface AuthCardProps {
  title: string;
  subtitle: string;
  children: React.ReactNode;
}

export function AuthCard({ title, subtitle, children }: AuthCardProps) {
  return (
    <div className="w-full max-w-[440px] bg-white dark:bg-surface border border-light-gray rounded-lg p-6 md:p-10 shadow-sm relative overflow-hidden">
      <div className="absolute top-0 left-0 w-full h-1 bg-vibrant-cyan" />
      <div className="text-center mb-8">
        <h1 className="text-headline-lg font-semibold text-primary dark:text-on-surface mb-2">
          {title}
        </h1>
        <p className="text-body-md text-on-surface-variant">{subtitle}</p>
      </div>
      {children}
    </div>
  );
}
