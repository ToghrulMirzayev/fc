"use client";

import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";

import { AppShell } from "@/components/AppShell";
import { PageHeader } from "@/components/PageHeader";
import { api, ApiError } from "@/lib/api";
import { useAuth } from "@/lib/useAuth";

type PaymentMethod = {
  key: string;
  label: string;
  operational: boolean;
  description: string;
};

type LookupResult =
  | {
      single_match: true;
      member: {
        id: string;
        full_name: string;
        phone: string;
        email: string | null;
        initials: string;
        status: string;
        active_membership: {
          id: string;
          plan_name: string;
          price: string;
          is_paid: boolean;
        } | null;
      };
    }
  | {
      single_match: false;
      candidates: {
        id: string;
        full_name: string;
        phone: string;
        initials: string;
      }[];
    };

export default function PaymentsPage() {
  const { user, isLoading: authLoading } = useAuth();
  const [activeTab, setActiveTab] = useState("cash");

  const { data: methodsData } = useQuery({
    queryKey: ["payment-methods"],
    queryFn: () => api<{ methods: PaymentMethod[] }>("/api/v1/payments/methods"),
    enabled: !!user,
  });

  if (authLoading || !user) {
    return (
      <AppShell>
        <div className="text-tertiary">Loading…</div>
      </AppShell>
    );
  }

  const methods = methodsData?.methods ?? [];
  const current = methods.find((m) => m.key === activeTab);

  return (
    <AppShell>
      <PageHeader crumbs={["Catalog", "Payments"]} title="Record payment" />

      <div className="mb-6 flex gap-1 rounded-md border border-subtle bg-card p-1">
        {methods.map((m) => (
          <button
            key={m.key}
            type="button"
            onClick={() => setActiveTab(m.key)}
            className={[
              "flex-1 rounded-sm px-4 py-2.5 text-md font-medium transition-colors",
              activeTab === m.key
                ? "bg-coral text-white"
                : m.operational
                ? "text-secondary hover:text-primary hover:bg-elev"
                : "text-tertiary hover:text-secondary hover:bg-elev",
            ].join(" ")}
          >
            <span className="flex items-center justify-center gap-1.5">
              {m.label}
              {!m.operational && (
                <span
                  className={[
                    "rounded-sm px-1.5 py-0.5 font-mono text-2xs uppercase tracking-caps",
                    activeTab === m.key
                      ? "bg-white/20 text-white"
                      : "bg-elev text-tertiary",
                  ].join(" ")}
                >
                  soon
                </span>
              )}
            </span>
          </button>
        ))}
      </div>

      {current?.operational ? <CashPaymentForm /> : <ComingSoonPanel method={current} />}
    </AppShell>
  );
}

function CashPaymentForm() {
  const [query, setQuery] = useState("");
  const [member, setMember] = useState<
    Extract<LookupResult, { single_match: true }>["member"] | null
  >(null);
  const [candidates, setCandidates] = useState<
    Extract<LookupResult, { single_match: false }>["candidates"]
  >([]);
  const [amount, setAmount] = useState("");
  const [note, setNote] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const lookup = useMutation({
    mutationFn: (q: string) =>
      api<LookupResult>(`/api/v1/members/lookup?q=${encodeURIComponent(q)}`),
    onSuccess: (r) => {
      setError(null);
      if (r.single_match) {
        setMember(r.member);
        setCandidates([]);
        if (r.member.active_membership?.price) {
          setAmount(r.member.active_membership.price);
        }
      } else {
        setMember(null);
        setCandidates(r.candidates);
      }
    },
    onError: (e: Error) => {
      setMember(null);
      setCandidates([]);
      const code = e instanceof ApiError ? e.detail || e.code : e.message;
      setError(
        code === "Member not found"
          ? "No member matched. Try a phone number, email, or full name."
          : "Lookup failed. Please try again.",
      );
    },
  });

  const selectCandidate = (id: string) => {
    lookup.mutate(id);
  };

  const recordPayment = useMutation({
    mutationFn: (payload: Record<string, unknown>) =>
      api<{ payment_id: string; membership_activated: boolean }>(
        "/api/v1/payments/cash",
        { method: "POST", body: JSON.stringify(payload) },
      ),
    onSuccess: (r) => {
      setSuccess(
        r.membership_activated
          ? "Payment recorded — the member's card is now active."
          : "Payment recorded.",
      );
      setError(null);
      setQuery("");
      setMember(null);
      setAmount("");
      setNote("");
    },
    onError: (e: Error) => {
      const code = e instanceof ApiError ? e.detail || e.code : e.message;
      setError(code || "Payment failed");
      setSuccess(null);
    },
  });

  const lookupSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) lookup.mutate(query.trim());
  };

  const recordSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!member) return;
    recordPayment.mutate({
      member_id: member.id,
      membership_id: member.active_membership?.id,
      amount: parseFloat(amount),
      note: note || null,
    });
  };

  return (
    <div className="grid grid-cols-[1fr_320px] gap-6">
      <div className="rounded-md border border-subtle bg-card p-6">
        <h2 className="mb-1 text-xl font-semibold tracking-tight text-primary">
          Cash payment
        </h2>
        <p className="mb-6 text-md text-secondary">
          Find the member, confirm details, then record the cash received.
          The card unlocks immediately.
        </p>

        <form onSubmit={lookupSubmit} className="mb-4 flex gap-2">
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Name, phone, email, or ID"
            className="flex-1 rounded-md border border-input bg-input-bg px-3 py-2.5 text-md text-primary placeholder:text-tertiary focus:border-coral focus:outline-none"
          />
          <button
            type="submit"
            disabled={lookup.isPending || !query.trim()}
            className="rounded-md border border-coral bg-coral px-4 py-2.5 text-md font-medium text-white hover:bg-coral-dim disabled:opacity-50"
          >
            {lookup.isPending ? "Searching…" : "Find"}
          </button>
        </form>

        {error && (
          <div className="mb-4 rounded-md border border-danger/30 bg-danger-soft p-3 text-md text-danger">
            {error}
          </div>
        )}

        {success && (
          <div className="mb-4 rounded-md border border-ozone/30 bg-ozone-soft p-3 text-md text-ozone">
            {success}
          </div>
        )}

        {candidates.length > 0 && (
          <div className="mb-4 border-t border-subtle pt-4">
            <div className="mb-2 font-mono text-xs uppercase tracking-caps text-tertiary">
              Multiple matches — pick one
            </div>
            <div className="space-y-2">
              {candidates.map((c) => (
                <button
                  key={c.id}
                  type="button"
                  onClick={() => selectCandidate(c.id)}
                  className="flex w-full items-center gap-2.5 rounded-md border border-subtle bg-elev px-3 py-2 text-left hover:bg-card-hover"
                >
                  <div className="flex h-7 w-7 items-center justify-center rounded-full bg-coral text-xs font-semibold text-white">
                    {c.initials}
                  </div>
                  <div className="flex-1">
                    <div className="text-md font-medium text-primary">
                      {c.full_name}
                    </div>
                    <div className="font-mono text-xs text-tertiary">
                      {c.phone}
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}

        {member && (
          <form onSubmit={recordSubmit} className="space-y-4 border-t border-subtle pt-5">
            <div>
              <div className="font-mono text-xs uppercase tracking-caps text-tertiary">
                Member
              </div>
              <div className="mt-1 text-md font-medium text-primary">
                {member.full_name}
              </div>
              <div className="font-mono text-sm text-tertiary">{member.phone}</div>
            </div>

            {member.active_membership ? (
              <div>
                <div className="font-mono text-xs uppercase tracking-caps text-tertiary">
                  Plan
                </div>
                <div className="mt-1 flex items-center gap-2 text-md">
                  <span className="font-medium text-primary">
                    {member.active_membership.plan_name}
                  </span>
                  {member.active_membership.is_paid ? (
                    <span className="pill pill-active">Paid</span>
                  ) : (
                    <span className="pill pill-pending">Awaiting payment</span>
                  )}
                </div>
              </div>
            ) : (
              <div className="rounded-md border border-warning/30 bg-warning-soft p-3 text-md text-warning">
                No active plan. Assign a plan from the member profile first.
              </div>
            )}

            <div>
              <label className="mb-2 block font-mono text-xs uppercase tracking-caps text-tertiary">
                Amount
              </label>
              <input
                type="number"
                step="0.01"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                required
                className="w-full rounded-md border border-input bg-input-bg px-3 py-2.5 text-md text-primary focus:border-coral focus:outline-none"
              />
            </div>

            <div>
              <label className="mb-2 block font-mono text-xs uppercase tracking-caps text-tertiary">
                Note <span className="text-dim">(optional)</span>
              </label>
              <input
                value={note}
                onChange={(e) => setNote(e.target.value)}
                placeholder="e.g. May cycle, partial payment, etc."
                className="w-full rounded-md border border-input bg-input-bg px-3 py-2.5 text-md text-primary placeholder:text-tertiary focus:border-coral focus:outline-none"
              />
            </div>

            <button
              type="submit"
              disabled={
                !amount ||
                !member.active_membership ||
                recordPayment.isPending
              }
              className="w-full rounded-md bg-coral px-4 py-3 text-md font-medium text-white hover:bg-coral-dim disabled:cursor-not-allowed disabled:opacity-50"
            >
              {recordPayment.isPending ? "Recording…" : "Record cash payment"}
            </button>
          </form>
        )}
      </div>

      <div className="rounded-md border border-subtle bg-card p-5">
        <div className="font-mono text-xs uppercase tracking-caps text-tertiary">
          How it works
        </div>
        <ol className="mt-3 space-y-3 text-md text-secondary">
          <li>
            <span className="font-mono text-coral">1.</span> Member gets a plan
            assigned in their profile.
          </li>
          <li>
            <span className="font-mono text-coral">2.</span> Until paid, the
            card is locked and they can't check in.
          </li>
          <li>
            <span className="font-mono text-coral">3.</span> Find the member
            here and record the cash.
          </li>
          <li>
            <span className="font-mono text-coral">4.</span> Card unlocks
            instantly — they can use the QR right away.
          </li>
        </ol>
      </div>
    </div>
  );
}

function ComingSoonPanel({ method }: { method?: PaymentMethod }) {
  if (!method) return null;
  return (
    <div className="rounded-md border border-subtle bg-card p-12">
      <div className="mx-auto max-w-md text-center">
        <div className="mx-auto mb-4 inline-flex items-center justify-center rounded-sm bg-coral-soft px-2.5 py-1">
          <span className="font-mono text-xs uppercase tracking-caps text-coral">
            Coming soon
          </span>
        </div>
        <h3 className="mb-3 text-xl font-semibold tracking-tight text-primary">
          {method.label}
        </h3>
        <p className="text-md text-secondary leading-relaxed">
          {method.description} We're actively working on this — it will be
          available in an upcoming release.
        </p>
        <p className="mt-6 text-sm text-tertiary">
          For now, please use the <span className="text-primary">Cash</span> tab.
        </p>
      </div>
    </div>
  );
}
