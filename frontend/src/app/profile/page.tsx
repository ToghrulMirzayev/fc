"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { AppShell } from "@/components/AppShell";
import { Button, PageHeader } from "@/components/PageHeader";
import { IconX } from "@/components/icons";
import { tokens } from "@/lib/api";
import { useAuth } from "@/lib/useAuth";

function Row({ label, value, mono }: { label: string; value: string; mono?: boolean }) {
  return (
    <div className="flex items-baseline justify-between border-b border-subtle py-2.5 text-base last:border-0">
      <span className="font-mono text-xs uppercase tracking-caps text-tertiary">
        {label}
      </span>
      <span
        className={`font-medium text-primary ${mono ? "font-mono" : ""}`}
      >
        {value}
      </span>
    </div>
  );
}

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
        actions={
          <Button onClick={() => setShowConfirm(true)}>Sign out</Button>
        }
      />

      <div className="grid grid-cols-[280px_1fr] gap-6">
        {/* Left: identity */}
        <div className="rounded-md border border-subtle bg-card p-6">
          <div
            className="mb-4 flex h-20 w-20 items-center justify-center rounded-full text-2xl font-semibold text-white"
            style={{
              background:
                "linear-gradient(135deg, var(--color-coral), var(--color-coral-dim))",
            }}
          >
            {initialsOf(user.full_name)}
          </div>
          <div className="text-xl font-semibold text-primary">
            {user.full_name}
          </div>
          <div className="mt-1 font-mono text-xs uppercase tracking-caps text-tertiary">
            {user.role}
          </div>
        </div>

        {/* Right: details */}
        <div className="rounded-md border border-subtle bg-card p-6">
          <div className="font-mono text-xs uppercase tracking-caps text-tertiary">
            Personal details
          </div>
          <div className="mt-3">
            <Row label="Full name" value={user.full_name} />
            <Row label="Email address" value={user.email} />
            <Row label="System role" value={user.role} />
          </div>

          <div className="mt-8 border-t border-subtle pt-6 font-mono text-xs uppercase tracking-caps text-tertiary">
            Workspace
          </div>
          <div className="mt-3">
            <Row label="Gym name" value={user.tenant_name || "—"} />
            <Row
              label="Workspace URL"
              mono
              value={
                user.tenant_slug
                  ? `${user.tenant_slug}.fitnesscourt.local`
                  : "—"
              }
            />
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
            className="w-full max-w-sm rounded-md border border-subtle bg-card p-6 shadow-frame"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-start justify-between">
              <div>
                <div className="font-mono text-xs uppercase tracking-caps text-tertiary">
                  Confirm
                </div>
                <h3 className="mt-1.5 text-xl font-semibold tracking-tight text-primary">
                  Sign out
                </h3>
              </div>
              <button
                type="button"
                onClick={() => setShowConfirm(false)}
                className="-mr-1 -mt-1 rounded-sm p-1 text-tertiary transition-colors hover:text-primary"
                aria-label="Close"
              >
                <IconX size={16} />
              </button>
            </div>
            <p className="mt-3 text-md text-secondary">
              Are you sure you want to sign out of your account?
            </p>
            <div className="mt-6 flex gap-2">
              <button
                type="button"
                onClick={() => setShowConfirm(false)}
                className="flex-1 justify-center rounded-md border border-subtle bg-card px-3.5 py-2 text-base font-medium text-primary transition-colors hover:border-strong hover:bg-card-hover"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={logout}
                className="flex-1 justify-center rounded-md border border-danger bg-danger px-3.5 py-2 text-base font-medium text-white transition-opacity hover:opacity-90"
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
