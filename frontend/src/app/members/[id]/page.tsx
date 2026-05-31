"use client";

import { useParams } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { AppShell } from "@/components/AppShell";
import { Button, PageHeader } from "@/components/PageHeader";
import { api, ApiError } from "@/lib/api";
import { invalidateMemberData } from "@/lib/invalidate";
import { useAuth } from "@/lib/useAuth";

type MemberDetail = {
  id: string;
  full_name: string;
  phone: string;
  email: string | null;
  telegram_user_id: number | null;
  locale: string;
  status: string;
  notes: string | null;
  initials: string;
  active_membership: {
    id: string;
    plan_name: string;
    plan_type: string;
    starts_on: string;
    expires_on: string;
    visit_limit: number | null;
    visits_remaining: number | null;
    status: string;
    days_left: number;
    is_paid: boolean;
  } | null;
};

type Plan = {
  id: string;
  name: string;
  type: string;
  price: string;
  duration_days: number;
  visit_limit: number | null;
};

type Visit = { id: string; method: string; checked_in_at: string };

export default function MemberProfilePage() {
  const params = useParams<{ id: string }>();
  const memberId = params.id;
  const qc = useQueryClient();
  const { user, isLoading: authLoading } = useAuth();
  const [linkingCode, setLinkingCode] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [showAssign, setShowAssign] = useState(false);
  const [showFreeze, setShowFreeze] = useState(false);
  const [freezeDays, setFreezeDays] = useState(14);
  const [freezeReason, setFreezeReason] = useState("");

  const { data: member } = useQuery({
    queryKey: ["member", memberId],
    queryFn: () => api<MemberDetail>(`/api/v1/members/${memberId}`),
    enabled: !!user,
  });

  const { data: visits } = useQuery({
    queryKey: ["member-visits", memberId],
    queryFn: () =>
      api<{ items: Visit[] }>(`/api/v1/members/${memberId}/visits`),
    enabled: !!user,
  });

  const { data: plansData } = useQuery({
    queryKey: ["plans"],
    queryFn: () => api<Plan[]>("/api/v1/plans"),
    enabled: !!user && showAssign,
  });

  const linkingMutation = useMutation({
    mutationFn: () =>
      api<{ code: string }>(`/api/v1/members/${memberId}/linking-code`, {
        method: "POST",
        body: "{}",
      }),
    onSuccess: (d) => setLinkingCode(d.code),
    onError: (e: Error) => setError(e.message),
  });

  // After any status-changing action we just re-GET the member and write
  // the fresh result into the cache. This re-renders the page immediately
  // (no F5) and doesn't depend on the POST's response body, so it works
  // even before the backend container is rebuilt.
  const refreshMember = async () => {
    const fresh = await api<MemberDetail>(`/api/v1/members/${memberId}`);
    qc.setQueryData(["member", memberId], fresh);
    invalidateMemberData(qc, memberId);
  };

  const assignPlan = useMutation({
    mutationFn: (planId: string) =>
      api(`/api/v1/members/${memberId}/assign-plan`, {
        method: "POST",
        body: JSON.stringify({ plan_id: planId }),
      }),
    onSuccess: async () => {
      setSuccess("Plan assigned. Card is locked until payment is recorded.");
      setShowAssign(false);
      setError(null);
      await refreshMember();
    },
    onError: (e: Error) =>
      setError(e instanceof ApiError ? e.detail || e.message : e.message),
  });

  const freezeMutation = useMutation({
    mutationFn: (args: { endsOn: string; reason: string | null }) =>
      api(`/api/v1/members/${memberId}/freeze`, {
        method: "POST",
        body: JSON.stringify({ ends_on: args.endsOn, reason: args.reason }),
      }),
    onSuccess: async () => {
      setShowFreeze(false);
      setError(null);
      await refreshMember();
    },
    onError: (e: Error) =>
      setError(e instanceof ApiError ? e.detail || e.message : e.message),
  });

  const resumeMutation = useMutation({
    mutationFn: () =>
      api(`/api/v1/members/${memberId}/resume`, {
        method: "POST",
        body: "{}",
      }),
    onSuccess: async () => {
      await refreshMember();
    },
  });

  if (authLoading || !user || !member) {
    return (
      <AppShell>
        <div className="text-tertiary">Loading…</div>
      </AppShell>
    );
  }

  const m = member;
  const am = m.active_membership;

  const copyMemberId = async () => {
    try {
      await navigator.clipboard.writeText(m.id);
      setSuccess("Member ID copied. Paste it on the Payments page.");
      setTimeout(() => setSuccess(null), 3000);
    } catch {
      // noop
    }
  };

  return (
    <AppShell>
      <PageHeader
        crumbs={["Members", m.full_name]}
        title={m.full_name}
        actions={
          <>
            {!am && (
              <Button
                variant="primary"
                onClick={() => setShowAssign(!showAssign)}
              >
                {showAssign
                  ? "Cancel"
                  : m.status === "expired"
                    ? "Renew"
                    : "Assign plan"}
              </Button>
            )}
            {am && !am.is_paid && (
              <Button variant="primary" onClick={copyMemberId}>
                Copy ID for payment
              </Button>
            )}
            {am?.status === "frozen" ? (
              <Button onClick={() => resumeMutation.mutate()}>Resume</Button>
            ) : am?.is_paid ? (
              <Button onClick={() => setShowFreeze(true)}>Freeze</Button>
            ) : null}
            <Button onClick={() => linkingMutation.mutate()}>
              {m.telegram_user_id ? "Re-link Telegram" : "Link Telegram"}
            </Button>
          </>
        }
      />

      {error && (
        <div className="mb-4 rounded-md border border-danger/30 bg-danger-soft px-3 py-2 text-md text-danger">
          {error}
        </div>
      )}
      {success && (
        <div className="mb-4 rounded-md border border-ozone/30 bg-ozone-soft px-3 py-2 text-md text-ozone">
          {success}
        </div>
      )}

      {linkingCode && (
        <div className="mb-4 rounded-md border border-coral/40 bg-coral-soft px-4 py-3">
          <div className="font-mono text-xs uppercase tracking-caps text-coral">
            One-time linking code · valid for 10 minutes
          </div>
          <div className="mt-1 text-3xl font-semibold tabular-nums text-primary">
            {linkingCode}
          </div>
          <div className="mt-1 text-sm text-secondary">
            Ask the member to send this to the Telegram bot.
          </div>
        </div>
      )}

      {showAssign && (
        <div className="mb-4 rounded-md border border-coral/30 bg-card p-4">
          <div className="mb-3 font-mono text-xs uppercase tracking-caps text-tertiary">
            {m.status === "expired" ? "Renew — choose a plan" : "Choose a plan"}
          </div>
          <div className="grid grid-cols-2 gap-3">
            {plansData?.map((p) => (
              <button
                key={p.id}
                type="button"
                onClick={() => assignPlan.mutate(p.id)}
                disabled={assignPlan.isPending}
                className="rounded-md border border-subtle bg-elev p-3 text-left hover:border-coral disabled:opacity-50"
              >
                <div className="font-medium text-primary">{p.name}</div>
                <div className="mt-1 font-mono text-sm text-tertiary">
                  {Number(p.price).toFixed(0)} · {p.duration_days}d{" "}
                  {p.visit_limit ? `· ${p.visit_limit} visits` : "· unlimited"}
                </div>
              </button>
            ))}
            {plansData?.length === 0 && (
              <div className="col-span-2 text-tertiary">
                No plans yet. Create one from the Plans page.
              </div>
            )}
          </div>
        </div>
      )}

      {showFreeze && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
          onClick={() => setShowFreeze(false)}
        >
          <div
            className="w-full max-w-md rounded-md border border-subtle bg-card p-6"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="font-mono text-xs uppercase tracking-caps text-tertiary">
              Freeze membership
            </div>
            <div className="mt-1 text-xl font-semibold text-primary">
              Choose freeze duration
            </div>
            <p className="mt-2 text-md text-secondary">
              The membership is paused and the expiry date is pushed back by the
              same number of days, so no paid time is lost.
            </p>

            <div className="mt-5 grid grid-cols-4 gap-2">
              {[7, 14, 30, 60].map((d) => (
                <button
                  key={d}
                  type="button"
                  onClick={() => setFreezeDays(d)}
                  className={`rounded-md border px-2 py-2 text-md font-medium transition-colors ${
                    freezeDays === d
                      ? "border-coral bg-coral-soft text-coral"
                      : "border-subtle bg-elev text-secondary hover:border-coral"
                  }`}
                >
                  {d}d
                </button>
              ))}
            </div>

            <div className="mt-4">
              <label className="font-mono text-xs uppercase tracking-caps text-tertiary">
                Custom days
              </label>
              <input
                type="number"
                min={1}
                max={365}
                value={freezeDays}
                onChange={(e) =>
                  setFreezeDays(Math.max(1, Number(e.target.value) || 1))
                }
                className="mt-1 w-full rounded-md border border-subtle bg-elev px-3 py-2 text-primary outline-none focus:border-coral"
              />
            </div>

            <div className="mt-4">
              <label className="font-mono text-xs uppercase tracking-caps text-tertiary">
                Reason (optional)
              </label>
              <input
                type="text"
                value={freezeReason}
                onChange={(e) => setFreezeReason(e.target.value)}
                placeholder="e.g. travel, injury"
                className="mt-1 w-full rounded-md border border-subtle bg-elev px-3 py-2 text-primary outline-none focus:border-coral"
              />
            </div>

            <div className="mt-6 flex justify-end gap-2">
              <Button onClick={() => setShowFreeze(false)}>Cancel</Button>
              <Button
                variant="primary"
                onClick={() => {
                  const d = new Date();
                  d.setDate(d.getDate() + freezeDays);
                  freezeMutation.mutate({
                    endsOn: d.toISOString().slice(0, 10),
                    reason: freezeReason.trim() || null,
                  });
                }}
              >
                {freezeMutation.isPending
                  ? "Freezing…"
                  : `Freeze for ${freezeDays}d`}
              </Button>
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-[280px_1fr] gap-6">
        <div className="rounded-md border border-subtle bg-card p-6">
          <div
            className="mb-4 flex h-20 w-20 items-center justify-center rounded-full text-2xl font-semibold text-white"
            style={{
              background:
                "linear-gradient(135deg, var(--color-coral), var(--color-coral-dim))",
            }}
          >
            {m.initials}
          </div>
          <div className="text-xl font-semibold text-primary">{m.full_name}</div>
          <div className="mb-5 font-mono text-sm text-tertiary">
            MBR_{m.id.slice(0, 8).toUpperCase()}
          </div>

          {[
            ["Phone", m.phone],
            ["Email", m.email || "—"],
            ["Status", m.status],
            ["Locale", m.locale],
          ].map(([k, v]) => (
            <div
              key={k}
              className="flex items-baseline justify-between border-b border-subtle py-2.5 text-base last:border-0"
            >
              <span className="font-mono text-xs uppercase tracking-caps text-tertiary">
                {k}
              </span>
              <span className="font-medium text-primary">{v}</span>
            </div>
          ))}

          {m.telegram_user_id && (
            <div className="mt-4 flex items-center gap-2.5 rounded-sm bg-elev p-2.5 font-mono text-sm text-ice">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                <path d="M21.5 4.5 18.4 19.7c-.2 1-.9 1.3-1.7.8l-4.7-3.5-2.3 2.2c-.3.3-.5.5-1 .5l.3-4.7L17.5 7c.4-.3-.1-.5-.5-.2L9.5 11.5l-4.6-1.4c-1-.3-1-.9.2-1.4L20 3.2c.9-.3 1.6.2 1.5 1.3z" />
              </svg>
              Telegram linked
            </div>
          )}
        </div>

        <div className="rounded-md border border-subtle bg-card p-6">
          {am ? (
            <>
              {!am.is_paid && (
                <div className="mb-5 rounded-md border border-warning/30 bg-warning-soft px-4 py-3">
                  <div className="flex items-center gap-2 font-mono text-xs uppercase tracking-caps text-warning">
                    🔒 Card locked · Awaiting payment
                  </div>
                  <div className="mt-1 text-md text-secondary">
                    The member can't check in until payment is recorded. Go to{" "}
                    <span className="text-primary">Payments</span> and record
                    the cash payment for this member.
                  </div>
                </div>
              )}

              <div className="mb-6 flex justify-between border-b border-subtle pb-6">
                <div>
                  <div className="font-mono text-xs uppercase tracking-caps text-tertiary">
                    {am.is_paid ? "Active plan" : "Pending plan"}
                  </div>
                  <div className="mt-1 text-2xl font-semibold tracking-tight text-primary">
                    {am.plan_name}
                  </div>
                  <div className="mt-3 flex gap-6 text-md">
                    {[
                      ["Started", am.starts_on],
                      ["Expires", am.expires_on],
                      ["Days left", `${am.days_left}`],
                    ].map(([k, v]) => (
                      <div key={k}>
                        <div className="font-mono text-xs uppercase tracking-caps text-tertiary">
                          {k}
                        </div>
                        <div className="mt-0.5 text-primary">{v}</div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              <div className="mb-4 font-mono text-xs uppercase tracking-caps text-tertiary">
                Recent activity
              </div>
              <div className="relative space-y-3">
                {visits?.items.slice(0, 6).map((v) => (
                  <div
                    key={v.id}
                    className="grid grid-cols-[12px_120px_1fr] items-start gap-3 text-md"
                  >
                    <div className="mt-1.5 h-2 w-2 rounded-full bg-coral" />
                    <span className="font-mono text-xs uppercase tracking-caps text-tertiary">
                      {new Date(v.checked_in_at).toLocaleString("en-US", {
                        month: "short",
                        day: "numeric",
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </span>
                    <div className="text-secondary">
                      <strong className="font-medium text-primary">
                        Check-in
                      </strong>{" "}
                      via {v.method.toUpperCase()}
                    </div>
                  </div>
                ))}
                {!visits?.items.length && (
                  <div className="text-tertiary">No visits yet.</div>
                )}
              </div>
            </>
          ) : (
            <div className="py-16 text-center">
              <div className="text-lg text-tertiary">No active plan</div>
              <p className="mt-2 text-md text-secondary">
                Assign a plan to get started. The member's card will be locked
                until payment is recorded.
              </p>
            </div>
          )}
        </div>
      </div>
    </AppShell>
  );
}
