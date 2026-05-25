"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { AppShell } from "@/components/AppShell";
import { Button, PageHeader } from "@/components/PageHeader";
import { IconPlus } from "@/components/icons";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/useAuth";

type Plan = {
  id: string;
  name: string;
  type: string;
  price: string;
  duration_days: number;
  visit_limit: number | null;
  max_freeze_days: number;
  max_freeze_count: number;
  is_active: boolean;
};

const PLAN_TYPE_LABELS: Record<string, string> = {
  unlimited_monthly: "Unlimited monthly",
  limited_visits: "Limited visits",
  yearly: "Yearly",
  one_time: "One-time",
  trial: "Trial",
};

export default function PlansPage() {
  const { user, isLoading: authLoading } = useAuth();
  const qc = useQueryClient();
  const [creating, setCreating] = useState(false);

  const { data: plans } = useQuery({
    queryKey: ["plans"],
    queryFn: () => api<Plan[]>("/api/v1/plans"),
    enabled: !!user,
  });

  const createPlan = useMutation({
    mutationFn: (payload: Record<string, unknown>) =>
      api("/api/v1/plans", { method: "POST", body: JSON.stringify(payload) }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["plans"] });
      setCreating(false);
    },
  });

  if (authLoading || !user) {
    return (
      <AppShell>
        <div className="text-tertiary">Loading…</div>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <PageHeader
        crumbs={["Catalog", "Plans"]}
        title="Membership plans"
        accent={plans ? `· ${plans.length}` : ""}
        actions={
          <Button
            variant="primary"
            icon={<IconPlus size={14} />}
            onClick={() => setCreating(true)}
          >
            New plan
          </Button>
        }
      />

      {creating && (
        <PlanForm
          onCancel={() => setCreating(false)}
          onSubmit={(p) => createPlan.mutate(p)}
          submitting={createPlan.isPending}
        />
      )}

      <div className="grid grid-cols-3 gap-4">
        {plans?.map((p) => (
          <div key={p.id} className="rounded-md border border-subtle bg-card p-5">
            <div className="mb-3 font-mono text-xs uppercase tracking-caps text-tertiary">
              {PLAN_TYPE_LABELS[p.type] || p.type}
            </div>
            <div className="text-xl font-semibold tracking-tight text-primary">
              {p.name}
            </div>
            <div className="mt-2 text-3xl font-semibold tabular-nums text-primary">
              {Number(p.price).toFixed(0)}
              <span className="ml-1 text-sm font-normal text-tertiary">
                / {p.duration_days}d
              </span>
            </div>
            <dl className="mt-4 space-y-1.5 text-sm">
              <div className="flex justify-between">
                <dt className="text-tertiary">Visits</dt>
                <dd className="text-primary">{p.visit_limit ?? "Unlimited"}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-tertiary">Max freeze</dt>
                <dd className="text-primary">
                  {p.max_freeze_days}d · {p.max_freeze_count}×
                </dd>
              </div>
            </dl>
          </div>
        ))}
        {plans && plans.length === 0 && !creating && (
          <div className="col-span-3 rounded-md border border-subtle bg-card p-8 text-center text-tertiary">
            No plans yet. Create your first one to start signing up members.
          </div>
        )}
      </div>
    </AppShell>
  );
}

function PlanForm({
  onCancel,
  onSubmit,
  submitting,
}: {
  onCancel: () => void;
  onSubmit: (p: Record<string, unknown>) => void;
  submitting: boolean;
}) {
  const [name, setName] = useState("");
  const [type, setType] = useState("unlimited_monthly");
  const [price, setPrice] = useState("60");
  const [durationDays, setDurationDays] = useState("30");
  const [visitLimit, setVisitLimit] = useState("");

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({
      name,
      type,
      price: parseFloat(price),
      duration_days: parseInt(durationDays, 10),
      visit_limit: visitLimit ? parseInt(visitLimit, 10) : null,
    });
  };

  const input =
    "rounded-md border border-input bg-input-bg px-3 py-2 text-md text-primary placeholder:text-tertiary focus:border-coral focus:outline-none";

  return (
    <form
      onSubmit={submit}
      className="mb-6 grid grid-cols-5 gap-3 rounded-md border border-coral/30 bg-card p-4"
    >
      <input
        required
        placeholder="Plan name"
        value={name}
        onChange={(e) => setName(e.target.value)}
        className={input}
      />
      <select
        value={type}
        onChange={(e) => setType(e.target.value)}
        className={input}
      >
        {Object.entries(PLAN_TYPE_LABELS).map(([k, v]) => (
          <option key={k} value={k}>
            {v}
          </option>
        ))}
      </select>
      <input
        required
        type="number"
        step="0.01"
        placeholder="Price"
        value={price}
        onChange={(e) => setPrice(e.target.value)}
        className={input}
      />
      <input
        required
        type="number"
        placeholder="Days"
        value={durationDays}
        onChange={(e) => setDurationDays(e.target.value)}
        className={input}
      />
      <input
        type="number"
        placeholder="Visits (blank = ∞)"
        value={visitLimit}
        onChange={(e) => setVisitLimit(e.target.value)}
        className={input}
      />
      <div className="col-span-5 flex justify-end gap-2">
        <Button onClick={onCancel}>Cancel</Button>
        <button
          type="submit"
          disabled={submitting}
          className="rounded-md border border-coral bg-coral px-3.5 py-2 text-base font-medium text-white hover:bg-coral-dim disabled:opacity-50"
        >
          {submitting ? "Creating…" : "Create plan"}
        </button>
      </div>
    </form>
  );
}
