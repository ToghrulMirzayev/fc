import { Sidebar } from "./Sidebar";

export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen bg-ink text-primary">
      <Sidebar />
      <main className="flex-1 overflow-x-hidden px-10 py-8">{children}</main>
    </div>
  );
}
