"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { Logo } from "@/components/Logo";
import { appName } from "@/lib/branding";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/**
 * Login step 1 — the user types their workspace name (the slug from
 * their gym's URL: `gymname.fitnesscourt.com`). We validate that the
 * workspace exists, then forward them to the password step.
 *
 * Mirrors Slack's flow: workspace first, then credentials.
 */
export default function WorkspacePage() {
  const router = useRouter();
  const [slug, setSlug] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const clean = slug.trim().toLowerCase().replace(/\s+/g, "-");
    if (!clean) return;
    setError(null);
    setPending(true);
    try {
      const res = await fetch(`${API_URL}/api/v1/public/workspace/${clean}`);
      if (res.status === 404) {
        setError(
          "We couldn't find that workspace. Check the spelling, or request a new one.",
        );
        return;
      }
      if (!res.ok) {
        setError("Something went wrong. Please try again.");
        return;
      }
      const data = await res.json();
      if (!data.is_active) {
        setError(
          "This workspace is being prepared. We'll be in touch once it's ready to use.",
        );
        return;
      }
      router.push(`/login/${clean}`);
    } catch {
      setError("Network error. Please try again.");
    } finally {
      setPending(false);
    }
  };

  return (
    <div className="flex min-h-screen flex-col bg-ink">
      <header className="border-b border-subtle px-12 py-6">
        <Logo size={32} />
      </header>

      <main className="flex flex-1 items-center justify-center px-6">
        <div className="w-full max-w-md">
          <h1 className="text-3xl font-semibold tracking-tight text-primary">
            Find your workspace
          </h1>
          <p className="mt-3 text-md text-secondary">
            Enter the name of your gym's workspace. It's the part before
            <span className="font-mono text-primary"> .{appName().toLowerCase().replace(/\s+/g, "-")}.com</span>.
          </p>

          <form onSubmit={onSubmit} className="mt-8 space-y-4">
            <div>
              <label className="mb-2 block font-mono text-xs uppercase tracking-caps text-tertiary">
                Workspace name
              </label>
              <div className="flex items-center rounded-md border border-input bg-input-bg focus-within:border-coral">
                <input
                  required
                  autoFocus
                  value={slug}
                  onChange={(e) => setSlug(e.target.value)}
                  placeholder="e.g. demo"
                  className="flex-1 bg-transparent px-3.5 py-2.5 text-md text-primary placeholder:text-tertiary focus:outline-none"
                />
                <span className="border-l border-subtle px-3 py-2.5 font-mono text-sm text-tertiary">
                  .{appName().toLowerCase().replace(/\s+/g, "-")}.com
                </span>
              </div>
            </div>

            {error && (
              <div className="rounded-md border border-danger/30 bg-danger-soft px-3 py-2 text-md text-danger">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={pending || !slug.trim()}
              className="w-full rounded-md bg-coral px-4 py-3 text-md font-medium text-white hover:bg-coral-dim disabled:cursor-not-allowed disabled:opacity-50"
            >
              {pending ? "Looking up…" : "Continue"}
            </button>
          </form>

          <div className="mt-10 border-t border-subtle pt-6 text-center">
            <p className="text-md text-secondary">
              New here?{" "}
              <Link href="/signup" className="font-medium text-coral hover:underline">
                Request a workspace
              </Link>
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}
