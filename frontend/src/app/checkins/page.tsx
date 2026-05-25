"use client";

import { useEffect, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { AppShell } from "@/components/AppShell";
import { Button, PageHeader } from "@/components/PageHeader";
import { IconSearch } from "@/components/icons";
import { api, ApiError } from "@/lib/api";
import { useAuth } from "@/lib/useAuth";

type ScanResult = {
  visit_id: string;
  member_id: string;
  member_name: string;
  initials: string;
  plan_name: string;
  visits_remaining: number | null;
};

type FeedItem = {
  id: string;
  member_id: string;
  member_name: string;
  initials: string;
  plan_name: string;
  visits_remaining: number | null;
  visit_limit: number | null;
  method: string;
  checked_in_at: string;
};

type Feed = { items: FeedItem[]; today_count: number };

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

const AVATAR_GRADIENTS = [
  "from-coral to-coral-dim",
  "from-ice to-[#2D5FA8]",
  "from-ozone to-ozone-dim",
  "from-warning to-[#B07424]",
];
function gradientFor(s: string): string {
  let h = 0;
  for (const c of s) h = (h * 31 + c.charCodeAt(0)) >>> 0;
  return AVATAR_GRADIENTS[h % AVATAR_GRADIENTS.length];
}

function relativeTime(iso: string): string {
  const diff = (Date.now() - Date.parse(iso)) / 1000;
  if (diff < 60) return "just now";
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  return new Date(iso).toLocaleTimeString("en-US", {
    hour: "2-digit",
    minute: "2-digit",
  });
}

/**
 * Translates backend check-in error codes into staff-friendly messages.
 * Shared by both QR scanner and the manual flow.
 */
const CHECKIN_ERRORS: Record<string, string> = {
  invalid_qr: "Invalid QR code",
  token_replay: "QR already used",
  wrong_tenant: "QR belongs to another gym",
  member_not_found: "Member not found",
  no_active_membership: "No active plan",
  payment_pending: "Card locked — payment not yet recorded",
  membership_frozen: "Plan is frozen",
  membership_expired: "Plan has expired",
  no_visits_left: "No visits remaining",
  anti_passback: "Already checked in recently",
};

export default function CheckinsPage() {
  const { user, isLoading: authLoading } = useAuth();
  const qc = useQueryClient();
  const inputRef = useRef<HTMLInputElement>(null);
  const [scanInput, setScanInput] = useState("");
  const [lastResult, setLastResult] = useState<ScanResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [manualOpen, setManualOpen] = useState(false);

  const { data: feed } = useQuery({
    queryKey: ["checkins-feed"],
    queryFn: () => api<Feed>("/api/v1/checkins/feed?limit=15"),
    enabled: !!user,
    refetchInterval: 5000,
  });

  const scanMutation = useMutation({
    mutationFn: (token: string) =>
      api<ScanResult>("/api/v1/checkins/scan", {
        method: "POST",
        body: JSON.stringify({ token }),
      }),
    onSuccess: (result) => {
      setLastResult(result);
      setError(null);
      setScanInput("");
      qc.invalidateQueries({ queryKey: ["checkins-feed"] });
      setTimeout(() => inputRef.current?.focus(), 100);
    },
    onError: (e: Error) => {
      const code = e instanceof ApiError ? e.detail || e.code : e.message;
      setError(CHECKIN_ERRORS[code] || "Check-in failed");
      setLastResult(null);
      setScanInput("");
      setTimeout(() => inputRef.current?.focus(), 100);
    },
  });

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  if (authLoading || !user) {
    return (
      <AppShell>
        <div className="text-tertiary">Loading…</div>
      </AppShell>
    );
  }

  const onScannerSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (scanInput.trim()) scanMutation.mutate(scanInput.trim());
  };

  return (
    <AppShell>
      <PageHeader
        crumbs={["Operations", "Check-ins"]}
        title="Front desk"
        actions={
          <Button
            icon={<IconSearch size={14} />}
            onClick={() => setManualOpen(true)}
          >
            Manual check-in
          </Button>
        }
      />

      {manualOpen && (
        <ManualCheckinModal
          onClose={() => setManualOpen(false)}
          onSuccess={(result) => {
            setLastResult(result);
            setError(null);
            setManualOpen(false);
            qc.invalidateQueries({ queryKey: ["checkins-feed"] });
          }}
          onError={(msg) => {
            setError(msg);
            setLastResult(null);
          }}
        />
      )}

      <div className="grid grid-cols-[340px_1fr] gap-6">
        <div className="relative flex flex-col items-center justify-center overflow-hidden rounded-lg border border-subtle bg-elev p-6">
          <div className="relative mb-5 h-56 w-56 overflow-hidden rounded-md border border-subtle bg-base">
            <div className="pointer-events-none absolute inset-3">
              <div className="absolute left-0 top-0 h-6 w-6 rounded-tl-sm border-2 border-b-0 border-r-0 border-coral" />
              <div className="absolute bottom-0 right-0 h-6 w-6 rounded-br-sm border-2 border-l-0 border-t-0 border-coral" />
            </div>
            <div
              className="absolute left-3 right-3 top-1/2 h-0.5 bg-gradient-to-r from-transparent via-coral to-transparent"
              style={{ boxShadow: "0 0 8px var(--color-accent)" }}
            />
          </div>

          <div className="flex items-center gap-2 font-mono text-xs uppercase tracking-capsxl text-coral">
            <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-coral" />
            {lastResult ? "Last scan accepted" : "Awaiting QR"}
          </div>
          <p className="mt-2 text-center text-sm text-tertiary">
            Scan a QR from the member's Telegram,
            <br />
            or use Manual check-in for offline members.
          </p>

          <form onSubmit={onScannerSubmit} className="mt-4 w-full">
            <input
              ref={inputRef}
              type="text"
              value={scanInput}
              onChange={(e) => setScanInput(e.target.value)}
              placeholder="QR token…"
              className="w-full rounded-md border border-input bg-input-bg px-3 py-2 text-center font-mono text-sm text-primary placeholder:text-tertiary focus:border-coral focus:outline-none"
            />
          </form>

          <div className="mt-5 flex w-full justify-between rounded-md bg-card px-3 py-2 font-mono text-xs uppercase tracking-caps text-tertiary">
            <span>Today</span>
            <span className="text-ozone">{feed?.today_count ?? 0} scanned</span>
          </div>

          {(lastResult || error) && (
            <div className="mt-4 w-full">
              {lastResult && (
                <div className="rounded-md border border-ozone/30 bg-ozone-soft p-3">
                  <div className="font-mono text-2xs uppercase tracking-caps text-ozone">
                    ✓ Accepted
                  </div>
                  <div className="mt-1 font-medium text-primary">
                    {lastResult.member_name}
                  </div>
                  <div className="font-mono text-xs text-tertiary">
                    {lastResult.plan_name}
                    {lastResult.visits_remaining !== null
                      ? ` · ${lastResult.visits_remaining} visits left`
                      : ""}
                  </div>
                </div>
              )}
              {error && (
                <div className="rounded-md border border-danger/30 bg-danger-soft p-3">
                  <div className="font-mono text-2xs uppercase tracking-caps text-danger">
                    ✗ Rejected
                  </div>
                  <div className="mt-1 text-md text-primary">{error}</div>
                </div>
              )}
            </div>
          )}
        </div>

        <div className="flex flex-col gap-3">
          <div className="flex items-end justify-between">
            <h2 className="text-lg font-semibold tracking-tight text-primary">
              Live feed
            </h2>
            <div className="font-mono text-sm text-tertiary">
              <strong className="text-ozone">{feed?.today_count ?? 0}</strong>{" "}
              today
            </div>
          </div>

          {feed?.items.length === 0 && (
            <div className="rounded-md border border-subtle bg-card p-8 text-center text-tertiary">
              No check-ins yet today.
            </div>
          )}

          {feed?.items.map((item, idx) => {
            const fresh = idx === 0;
            return (
              <div
                key={item.id}
                className={[
                  "flex items-center gap-3.5 rounded-md border p-3.5",
                  fresh
                    ? "border-coral/40 bg-coral-soft"
                    : "border-subtle bg-card",
                ].join(" ")}
              >
                <span
                  className={`w-14 shrink-0 font-mono text-sm ${
                    fresh ? "text-coral" : "text-tertiary"
                  }`}
                >
                  {relativeTime(item.checked_in_at)}
                </span>
                <div
                  className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-gradient-to-br ${gradientFor(item.member_id)} text-xs font-semibold text-white`}
                >
                  {item.initials}
                </div>
                <div className="min-w-0 flex-1">
                  <div className="truncate font-medium text-primary">
                    {item.member_name}
                  </div>
                  <div className="truncate font-mono text-sm text-tertiary">
                    {item.plan_name}
                  </div>
                </div>
                <span className="rounded-sm bg-elev px-2 py-1 font-mono text-sm text-secondary">
                  {item.visit_limit !== null && item.visits_remaining !== null
                    ? `${item.visits_remaining} left`
                    : "∞"}
                </span>
                <span className="font-mono text-2xs uppercase tracking-caps text-tertiary">
                  {item.method}
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </AppShell>
  );
}

/**
 * Manual check-in flow.
 *
 * Member search → confirm details → submit. Reuses the same lookup endpoint
 * the payments page uses, then calls POST /api/v1/checkins/manual/{member_id}.
 *
 * Surfaces backend error codes (no_active_membership, payment_pending,
 * membership_frozen, etc.) using the same translation table as QR scans.
 */
function ManualCheckinModal({
  onClose,
  onSuccess,
  onError,
}: {
  onClose: () => void;
  onSuccess: (r: ScanResult) => void;
  onError: (msg: string) => void;
}) {
  const [query, setQuery] = useState("");
  const [member, setMember] = useState<
    Extract<LookupResult, { single_match: true }>["member"] | null
  >(null);
  const [candidates, setCandidates] = useState<
    Extract<LookupResult, { single_match: false }>["candidates"]
  >([]);
  const [error, setError] = useState<string | null>(null);

  const lookup = useMutation({
    mutationFn: (q: string) =>
      api<LookupResult>(`/api/v1/members/lookup?q=${encodeURIComponent(q)}`),
    onSuccess: (r) => {
      setError(null);
      if (r.single_match) {
        setMember(r.member);
        setCandidates([]);
      } else {
        setMember(null);
        setCandidates(r.candidates);
      }
    },
    onError: () => {
      setMember(null);
      setCandidates([]);
      setError("No member matched. Try a phone number, email, or full name.");
    },
  });

  const checkin = useMutation({
    mutationFn: (memberId: string) =>
      api<{
        visit_id: string;
        member_name: string;
        plan_name: string;
        visits_remaining: number | null;
      }>(`/api/v1/checkins/manual/${memberId}`, {
        method: "POST",
        body: "{}",
      }),
    onSuccess: (result) => {
      // The manual endpoint returns slightly different shape from scan,
      // so we normalize before bubbling up to the parent's success state.
      onSuccess({
        visit_id: result.visit_id,
        member_id: member!.id,
        member_name: result.member_name,
        initials: member!.initials,
        plan_name: result.plan_name,
        visits_remaining: result.visits_remaining,
      });
    },
    onError: (e: Error) => {
      const code = e instanceof ApiError ? e.detail || e.code : e.message;
      onError(CHECKIN_ERRORS[code] || "Check-in failed");
    },
  });

  const lookupSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) lookup.mutate(query.trim());
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 px-4"
      onClick={onClose}
    >
      <div
        className="w-full max-w-lg rounded-lg border border-subtle bg-card p-6 shadow-frame"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-1 flex items-start justify-between">
          <h2 className="text-xl font-semibold tracking-tight text-primary">
            Manual check-in
          </h2>
          <button
            type="button"
            onClick={onClose}
            className="text-tertiary hover:text-primary"
            aria-label="Close"
          >
            ✕
          </button>
        </div>
        <p className="mb-6 text-md text-secondary">
          Use this when the member doesn't have their QR — phone died, app
          glitched, or they're new. We'll log the visit as manual.
        </p>

        <form onSubmit={lookupSubmit} className="mb-4 flex gap-2">
          <input
            autoFocus
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
                  onClick={() => lookup.mutate(c.id)}
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
          <div className="border-t border-subtle pt-5">
            <div className="flex items-center gap-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-coral text-md font-semibold text-white">
                {member.initials}
              </div>
              <div className="flex-1">
                <div className="text-md font-medium text-primary">
                  {member.full_name}
                </div>
                <div className="font-mono text-sm text-tertiary">
                  {member.phone}
                </div>
              </div>
              {member.active_membership ? (
                member.active_membership.is_paid ? (
                  <span className="pill pill-active">Paid</span>
                ) : (
                  <span className="pill pill-pending">Awaiting payment</span>
                )
              ) : (
                <span className="pill pill-expired">No plan</span>
              )}
            </div>

            {member.active_membership && (
              <div className="mt-3 text-md text-secondary">
                Plan:{" "}
                <span className="text-primary">
                  {member.active_membership.plan_name}
                </span>
              </div>
            )}

            <button
              type="button"
              onClick={() => checkin.mutate(member.id)}
              disabled={
                checkin.isPending ||
                !member.active_membership ||
                !member.active_membership.is_paid
              }
              className="mt-5 w-full rounded-md bg-coral px-4 py-3 text-md font-medium text-white hover:bg-coral-dim disabled:cursor-not-allowed disabled:opacity-50"
            >
              {checkin.isPending ? "Checking in…" : "Check in now"}
            </button>

            {member.active_membership && !member.active_membership.is_paid && (
              <p className="mt-2 text-center text-sm text-warning">
                Record payment first to unlock check-in.
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
