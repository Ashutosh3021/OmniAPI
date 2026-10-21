import { DashboardShell } from "@/components/shell/DashboardShell";
import { ProtectedRoute } from "@/components/shared/ProtectedRoute";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <ProtectedRoute>
      <DashboardShell>{children}</DashboardShell>
    </ProtectedRoute>
  );
}
