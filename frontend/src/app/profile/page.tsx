"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { AppShell } from "@/components/AppShell";
import { PageHeader } from "@/components/PageHeader";
import { tokens } from "@/lib/api";
import { useAuth } from "@/lib/useAuth";

function initialsOf(name: string): string {
  const parts = name.trim().split(/\s+/);
  if (parts.length === 0) return "?";
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

export default function ProfilePage() {
  const router = useRouter();
  const { user, isLoading } = useAuth();
  const [showConfirm, setShowConfirm] = useState(false);

  const logout = () => {
    tokens.clear();
    const targetUrl = user?.tenant_slug ? `/login/${user.tenant_slug}` : "/login";
    router.replace(targetUrl);
  };

  if (isLoading || !user) {
    return (
      <AppShell>
        <div className="text-tertiary">Loading…</div>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <PageHeader
        crumbs={["Settings", "My Profile"]}
        title="My Profile"
      />

      <div className="grid grid-cols-[280px_1fr] gap-6">
        {/* Left Side: Avatar and Logout */}
        <div className="flex flex-col items-center rounded-md border border-subtle bg-card p-6">
          <div
            className="mb-4 flex h-24 w-24 items-center justify-center rounded-full text-3xl font-semibold text-white"
            style={{
              background:
                "linear-gradient(135deg, var(--color-coral), var(--color-coral-dim))",
            }}
          >
            {initialsOf(user.full_name)}
          </div>
          <div className="text-center text-xl font-semibold text-primary">
            {user.full_name}
          </div>
          <div className="mb-6 font-mono text-xs uppercase tracking-caps text-tertiary">
            {user.role}
          </div>
          <button
            type="button"
            onClick={() => setShowConfirm(true)}
            className="w-full rounded-md bg-danger py-2.5 text-md font-medium text-white transition-opacity hover:opacity-90"
          >
            Sign Out
          </button>
        </div>

        {/* Right Side: Profile Details */}
        <div className="rounded-md border border-subtle bg-card p-6">
          <h2 className="mb-4 border-b border-subtle pb-2 text-lg font-semibold tracking-tight text-primary">
            Personal Details
          </h2>
          <div className="space-y-4">
            <div>
              <label className="mb-1 block font-mono text-xs uppercase tracking-caps text-tertiary">
                Full Name
              </label>
              <div className="text-md font-medium text-primary">
                {user.full_name}
              </div>
            </div>
            <div>
              <label className="mb-1 block font-mono text-xs uppercase tracking-caps text-tertiary">
                Email Address
              </label>
              <div className="text-md font-medium text-primary">
                {user.email}
              </div>
            </div>
            <div>
              <label className="mb-1 block font-mono text-xs uppercase tracking-caps text-tertiary">
                System Role
              </label>
              <div className="text-md font-medium capitalize text-primary">
                {user.role}
              </div>
            </div>
          </div>

          <h2 className="mb-4 mt-8 border-b border-subtle pb-2 text-lg font-semibold tracking-tight text-primary">
            Workspace Details
          </h2>
          <div className="space-y-4">
            <div>
              <label className="mb-1 block font-mono text-xs uppercase tracking-caps text-tertiary">
                Gym Name
              </label>
              <div className="text-md font-medium text-primary">
                {user.tenant_name || "—"}
              </div>
            </div>
            <div>
              <label className="mb-1 block font-mono text-xs uppercase tracking-caps text-tertiary">
                Workspace URL / Slug
              </label>
              <div className="font-mono text-md font-medium text-primary">
                {user.tenant_slug ? `${user.tenant_slug}.fitnesscourt.local` : "—"}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Sign Out Confirmation Modal */}
      {showConfirm && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 px-4 backdrop-blur-sm"
          onClick={() => setShowConfirm(false)}
        >
          <div
            className="w-full max-w-sm rounded-lg border border-subtle bg-card p-6 shadow-frame"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-start justify-between">
              <h3 className="text-xl font-semibold tracking-tight text-primary">
                Sign out
              </h3>
              <button
                type="button"
                onClick={() => setShowConfirm(false)}
                className="text-tertiary hover:text-primary transition-colors"
                aria-label="Close"
              >
                ✕
              </button>
            </div>
            <p className="mt-3 text-md text-secondary">
              Are you sure you want to sign out of your account?
            </p>
            <div className="mt-6 flex gap-3">
              <button
                type="button"
                onClick={() => setShowConfirm(false)}
                className="flex-1 rounded-md border border-subtle bg-elev px-4 py-2.5 text-md font-medium text-primary hover:bg-card-hover transition-colors text-center"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={logout}
                className="flex-1 rounded-md bg-danger px-4 py-2.5 text-md font-medium text-white transition-opacity hover:opacity-90 text-center"
              >
                Sign out
              </button>
            </div>
          </div>
        </div>
      )}
    </AppShell>
  );
}
