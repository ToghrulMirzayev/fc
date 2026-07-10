"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { Logo } from "@/components/Logo";
import { ThemeToggle } from "@/components/ThemeToggle";
import { appName } from "@/lib/branding";
import { Footer } from "@/components/Footer";

type BillingPlan = {
  tier: string;
  name: string;
  tagline: string;
  monthly_price_eur: number;
  member_cap: number | null;
  admin_seats: number | null;
  branches: number | null;
  features: string[];
  is_custom: boolean;
  is_trial: boolean;
  trial_days: number | null;
  highlight: boolean;
};

type Discount = {
  active: boolean;
  percent?: string;
  message?: string;
};

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function SignupPage() {
  const [plans, setPlans] = useState<BillingPlan[]>([]);
  const [discount, setDiscount] = useState<Discount>({ active: false });
  const [selectedTier, setSelectedTier] = useState<string>("basic");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<{
    welcome_message: string;
    tenant_url: string;
  } | null>(null);

  const [form, setForm] = useState({
    full_name: "",
    email: "",
    phone: "",
    company_name: "",
    country: "Azerbaijan",
    city: "",
    estimated_members: "1-100",
    notes: "",
  });

  useEffect(() => {
    fetch(`${API_URL}/api/v1/public/billing-plans`)
      .then((r) => r.json())
      .then((d) => setPlans(d.plans))
      .catch(() => {});
    fetch(`${API_URL}/api/v1/public/discount`)
      .then((r) => r.json())
      .then(setDiscount)
      .catch(() => {});
  }, []);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const res = await fetch(`${API_URL}/api/v1/public/signup`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...form, interested_tier: selectedTier }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        if (body.detail === "email_already_submitted") {
          setError(
            "We've already received a request for this email. Our team will be in touch shortly.",
          );
        } else {
          setError("Something went wrong. Please try again.");
        }
        return;
      }
      const data = await res.json();
      setResult(data);
    } catch {
      setError("Network error. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  const renderedDiscount =
    discount.active && discount.percent
      ? (discount.message || "Get {percent}% off your first 3 months.").replace(
          "{percent}",
          discount.percent,
        )
      : null;

  if (result) {
    return (
      <div className="min-h-screen bg-ink">
        <header className="flex items-center justify-between border-b border-subtle px-8 py-5">
          <Logo size={32} />
          <ThemeToggleInline />
        </header>
        <main className="mx-auto max-w-2xl px-6 py-20">
          <div className="mb-6 inline-flex h-12 w-12 items-center justify-center rounded-full bg-ozone-soft">
            <span className="font-mono text-lg font-semibold text-ozone">✓</span>
          </div>
          <h1 className="text-4xl font-semibold tracking-tight text-primary">
            Thanks — we've got your request.
          </h1>
          <div className="mt-6 whitespace-pre-line text-md text-secondary leading-relaxed">
            {result.welcome_message}
          </div>
          <div className="mt-8 rounded-md border border-coral/40 bg-coral-soft p-5">
            <div className="font-mono text-xs uppercase tracking-caps text-coral">
              Your reserved workspace
            </div>
            <div className="mt-1 break-all font-mono text-md text-primary">
              {result.tenant_url}
            </div>
            <div className="mt-2 text-sm text-secondary">
              This address is yours. We'll activate it once we've reviewed
              your application.
            </div>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-ink flex flex-col">
      <header className="flex items-center justify-between border-b border-subtle px-8 py-5">
        <Logo size={32} />
        <div className="flex items-center gap-4">
          <ThemeToggleInline />
          <Link
            href="/login"
            className="text-md font-medium text-secondary hover:text-coral"
          >
            Already part of the family? Sign in →
          </Link>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-6 py-16">
        <div className="mx-auto mb-12 max-w-3xl text-center">
          <h1 className="text-5xl font-semibold tracking-tight text-primary">
            Run your gym, not your software.
          </h1>
          <p className="mt-5 text-lg text-secondary leading-relaxed">
            {appName()} is a complete management platform for gyms and fitness
            studios. Memberships, check-ins, payments, and member self-service
            in one place — designed to be fast for staff and effortless for
            members.
          </p>
          {renderedDiscount && (
            <div className="mt-7 inline-flex items-center gap-2 rounded-md border border-coral/40 bg-coral-soft px-4 py-2 font-mono text-sm uppercase tracking-caps text-coral">
              🎉 {renderedDiscount}
            </div>
          )}
        </div>

        {/* Pricing tiers */}
        <div className="mb-6">
          <h2 className="text-2xl font-semibold tracking-tight text-primary">
            Plans for studio owners
          </h2>
          <p className="mt-1 max-w-3xl text-md text-secondary">
            Every plan starts with a free 14-day trial — no card required. Tiers
            scale on admin & trainer seats, locations, AI insights, Telegram
            automation, and access-control hardware, not just member count.
          </p>
        </div>

        <div className="mb-16 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {plans.map((p) => {
            const selected = selectedTier === p.tier;
            const cap =
              p.member_cap === null
                ? "Unlimited"
                : p.member_cap.toLocaleString();
            const seats =
              p.admin_seats === null ? "Unlimited" : String(p.admin_seats);
            const locations =
              p.branches === null ? "Unlimited" : String(p.branches);
            return (
              <button
                key={p.tier}
                type="button"
                onClick={() => setSelectedTier(p.tier)}
                className={[
                  "relative flex flex-col rounded-md border p-5 text-left transition-colors",
                  selected
                    ? "border-coral bg-coral-soft"
                    : p.highlight
                      ? "border-coral/40 bg-card hover:border-coral"
                      : "border-subtle bg-card hover:border-strong",
                ].join(" ")}
              >
                <div className="mb-3 flex items-center justify-between gap-2">
                  <div className="font-mono text-xs uppercase tracking-caps text-tertiary">
                    {p.name}
                  </div>
                  {p.highlight ? (
                    <span className="rounded-sm bg-coral-soft px-1.5 py-0.5 font-mono text-2xs uppercase tracking-caps text-coral">
                      Most popular
                    </span>
                  ) : p.is_trial ? (
                    <span className="rounded-sm bg-ozone-soft px-1.5 py-0.5 font-mono text-2xs uppercase tracking-caps text-ozone">
                      {p.trial_days}-day trial
                    </span>
                  ) : p.is_custom ? (
                    <span className="rounded-sm bg-elev px-1.5 py-0.5 font-mono text-2xs uppercase tracking-caps text-tertiary">
                      Custom
                    </span>
                  ) : null}
                </div>

                <div className="text-2xl font-semibold tabular-nums text-primary">
                  {p.is_custom ? (
                    <span className="text-lg text-tertiary">Let's talk</span>
                  ) : p.is_trial ? (
                    <>
                      Free
                      <span className="ml-1.5 text-sm font-normal text-tertiary">
                        for {p.trial_days} days
                      </span>
                    </>
                  ) : (
                    <>
                      €{p.monthly_price_eur}
                      <span className="ml-1 text-sm font-normal text-tertiary">
                        /mo
                      </span>
                    </>
                  )}
                </div>

                <p className="mt-2 text-sm text-secondary">{p.tagline}</p>

                <div className="mt-4 grid grid-cols-3 gap-2 border-y border-subtle py-3 text-center">
                  {[
                    ["Members", cap],
                    ["Seats", seats],
                    ["Locations", locations],
                  ].map(([label, value]) => (
                    <div key={label}>
                      <div className="text-sm font-semibold tabular-nums text-primary">
                        {value}
                      </div>
                      <div className="mt-0.5 font-mono text-2xs uppercase tracking-caps text-tertiary">
                        {label}
                      </div>
                    </div>
                  ))}
                </div>

                <ul className="mt-4 space-y-1.5 text-sm">
                  {p.features.map((f) => (
                    <li key={f} className="flex gap-2 text-secondary">
                      <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-coral" />
                      <span>{f}</span>
                    </li>
                  ))}
                </ul>
              </button>
            );
          })}
        </div>

        {/* Signup form */}
        <form
          onSubmit={submit}
          className="mx-auto max-w-2xl rounded-lg border border-subtle bg-card p-8"
        >
          <h2 className="mb-1 text-2xl font-semibold tracking-tight text-primary">
            Request a workspace
          </h2>
          <p className="mb-8 text-md text-secondary">
            Tell us about your gym. We'll set up your workspace and reach out
            within 1-2 business days with onboarding instructions.
          </p>

          <div className="grid grid-cols-2 gap-4">
            <Field label="Your name" required>
              <input
                required
                value={form.full_name}
                onChange={(e) =>
                  setForm({ ...form, full_name: e.target.value })
                }
                className={inputCls}
              />
            </Field>
            <Field label="Email" required>
              <input
                required
                type="email"
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                className={inputCls}
              />
            </Field>
            <Field label="Phone" required>
              <input
                required
                value={form.phone}
                onChange={(e) => setForm({ ...form, phone: e.target.value })}
                placeholder="+994 50 …"
                className={inputCls}
              />
            </Field>
            <Field label="Gym / company name" required>
              <input
                required
                value={form.company_name}
                onChange={(e) =>
                  setForm({ ...form, company_name: e.target.value })
                }
                className={inputCls}
              />
            </Field>
            <Field label="Country" required>
              <input
                required
                value={form.country}
                onChange={(e) => setForm({ ...form, country: e.target.value })}
                className={inputCls}
              />
            </Field>
            <Field label="City">
              <input
                value={form.city}
                onChange={(e) => setForm({ ...form, city: e.target.value })}
                className={inputCls}
              />
            </Field>
            <Field label="Estimated members" required>
              <select
                value={form.estimated_members}
                onChange={(e) =>
                  setForm({ ...form, estimated_members: e.target.value })
                }
                className={inputCls}
              >
                <option>1-100</option>
                <option>100-300</option>
                <option>300-1000</option>
                <option>1000-5000</option>
                <option>5000+</option>
              </select>
            </Field>
            <Field label="Selected plan">
              <div className="rounded-md border border-subtle bg-elev px-3 py-2.5 text-md text-primary">
                {plans.find((p) => p.tier === selectedTier)?.name || "—"}
              </div>
            </Field>
          </div>

          <div className="mt-4">
            <Field label="Anything else we should know?">
              <textarea
                rows={3}
                value={form.notes}
                onChange={(e) => setForm({ ...form, notes: e.target.value })}
                className={inputCls + " resize-none"}
              />
            </Field>
          </div>

          {error && (
            <div className="mt-4 rounded-md border border-danger/30 bg-danger-soft px-3 py-2 text-md text-danger">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={submitting}
            className="mt-6 w-full rounded-md bg-coral px-4 py-3 text-md font-medium text-white hover:bg-coral-dim disabled:cursor-not-allowed disabled:opacity-50"
          >
            {submitting ? "Submitting…" : "Submit request"}
          </button>

          <p className="mt-3 text-center text-sm text-tertiary">
            By creating an account you agree to our{" "}
            <Link href="/terms" className="underline hover:text-coral">
              Terms of Service
            </Link>{" "}
            and acknowledge our{" "}
            <Link href="/privacy" className="underline hover:text-coral">
              Privacy Policy
            </Link>.
          </p>
        </form>
      </main>
      <Footer />
    </div>
  );
}

const inputCls =
  "w-full rounded-md border border-input bg-input-bg px-3 py-2.5 text-md text-primary placeholder:text-tertiary focus:border-coral focus:outline-none";

function Field({
  label,
  required,
  children,
}: {
  label: string;
  required?: boolean;
  children: React.ReactNode;
}) {
  return (
    <div>
      <label className="mb-2 block font-mono text-xs uppercase tracking-caps text-tertiary">
        {label}
        {required && <span className="text-coral"> *</span>}
      </label>
      {children}
    </div>
  );
}

// Theme toggle without the sidebar wrapper, for use in public headers.
function ThemeToggleInline() {
  return <ThemeToggle variant="compact" />;
}
