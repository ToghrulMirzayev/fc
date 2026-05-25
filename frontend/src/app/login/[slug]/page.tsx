"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { Logo } from "@/components/Logo";
import { api, login } from "@/lib/api";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type Workspace = { slug: string; name: string; is_active: boolean };

/**
 * Login step 2 — credentials for the resolved workspace.
 *
 * The workspace is validated again on mount (cheap GET) so a stale or
 * shared link doesn't surface a confusing error. On success, redirect
 * to the dashboard.
 */
export default function CredentialsPage() {
  const params = useParams<{ slug: string }>();
  const slug = params.slug;
  const router = useRouter();
  const [workspace, setWorkspace] = useState<Workspace | null>(null);
  const [notFound, setNotFound] = useState(false);

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  useEffect(() => {
    fetch(`${API_URL}/api/v1/public/workspace/${slug}`)
      .then(async (r) => {
        if (r.status === 404) {
          setNotFound(true);
          return null;
        }
        return r.ok ? r.json() : null;
      })
      .then((data) => {
        if (data) setWorkspace(data);
      });
  }, [slug]);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setPending(true);
    try {
      await login(email, password);
      router.push("/");
    } catch (e) {
      const msg = (e as Error)?.message?.toLowerCase() || "";
      if (msg.includes("tenant_pending")) {
        setError(
          "This workspace is being prepared. We'll reach out once it's ready.",
        );
      } else {
        setError("Email or password didn't match. Please try again.");
      }
    } finally {
      setPending(false);
    }
  };

  if (notFound) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-ink px-6">
        <div className="w-full max-w-md text-center">
          <Logo size={32} />
          <h1 className="mt-8 text-2xl font-semibold tracking-tight text-primary">
            Workspace not found
          </h1>
          <p className="mt-3 text-md text-secondary">
            We couldn't find <span className="font-mono text-primary">{slug}</span>.
          </p>
          <Link
            href="/login"
            className="mt-6 inline-block font-medium text-coral hover:underline"
          >
            ← Try another workspace
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen flex-col bg-ink">
      <header className="border-b border-subtle px-12 py-6">
        <Logo size={32} />
      </header>

      <main className="flex flex-1 items-center justify-center px-6">
        <div className="w-full max-w-md">
          <div className="mb-2 font-mono text-xs uppercase tracking-caps text-coral">
            Step 2 of 2
          </div>
          {workspace ? (
            <>
              <h1 className="text-3xl font-semibold tracking-tight text-primary">
                Sign in to {workspace.name}
              </h1>
              <p className="mt-3 text-md text-secondary">
                Workspace:{" "}
                <span className="font-mono text-primary">{workspace.slug}</span>
              </p>
            </>
          ) : (
            <div className="h-16 animate-pulse rounded-md bg-card" />
          )}

          <form onSubmit={onSubmit} className="mt-8 space-y-4">
            <div>
              <label className="mb-2 block font-mono text-xs uppercase tracking-caps text-tertiary">
                Email
              </label>
              <input
                required
                type="email"
                autoComplete="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full rounded-md border border-input bg-input-bg px-3.5 py-2.5 text-md text-primary placeholder:text-tertiary focus:border-coral focus:outline-none"
                placeholder="you@example.com"
              />
            </div>

            <div>
              <label className="mb-2 block font-mono text-xs uppercase tracking-caps text-tertiary">
                Password
              </label>
              <input
                required
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full rounded-md border border-input bg-input-bg px-3.5 py-2.5 text-md text-primary placeholder:text-tertiary focus:border-coral focus:outline-none"
                placeholder="••••••••"
              />
            </div>

            {error && (
              <div className="rounded-md border border-danger/30 bg-danger-soft px-3 py-2 text-md text-danger">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={pending}
              className="w-full rounded-md bg-coral px-4 py-3 text-md font-medium text-white hover:bg-coral-dim disabled:cursor-not-allowed disabled:opacity-50"
            >
              {pending ? "Signing in…" : "Sign in"}
            </button>
          </form>

          <Link
            href="/login"
            className="mt-6 inline-block text-sm text-tertiary hover:text-primary"
          >
            ← Different workspace
          </Link>
        </div>
      </main>
    </div>
  );
}
