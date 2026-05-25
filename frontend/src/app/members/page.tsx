"use client";

import Link from "next/link";
import { useSearchParams, useRouter } from "next/navigation";
import { useState, Suspense } from "react";
import { useQuery } from "@tanstack/react-query";

import { AppShell } from "@/components/AppShell";
import { Button, PageHeader } from "@/components/PageHeader";
import { IconFilter, IconPlus } from "@/components/icons";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/useAuth";

type MemberRow = {
  id: string;
  full_name: string;
  phone: string;
  initials: string;
  status: "active" | "frozen" | "expired" | "inactive";
  plan_name: string | null;
  plan_type: string | null;
  expires_on: string | null;
  days_left: number | null;
  visits_remaining: number | null;
  visit_limit: number | null;
};

type MembersList = {
  items: MemberRow[];
  total: number;
  counts_by_status: Record<string, number>;
};

const AVATAR_GRADIENTS = [
  "from-coral to-coral-dim",
  "from-ice to-[#2D5FA8]",
  "from-ozone to-ozone-dim",
  "from-warning to-[#B07424]",
  "from-[#C77DFF] to-[#6C32A8]",
];
function gradientFor(s: string): string {
  let h = 0;
  for (const c of s) h = (h * 31 + c.charCodeAt(0)) >>> 0;
  return AVATAR_GRADIENTS[h % AVATAR_GRADIENTS.length];
}

function pillClass(status: string): string {
  switch (status) {
    case "active":
      return "pill pill-active";
    case "frozen":
      return "pill pill-frozen";
    case "expired":
      return "pill pill-expired";
    default:
      return "pill pill-trial";
  }
}

function MembersPageInner() {
  const params = useSearchParams();
  const router = useRouter();
  const { user, isLoading: authLoading } = useAuth();

  const statusFilter = params.get("status") || "all";
  const [search, setSearch] = useState(params.get("q") || "");

  const { data } = useQuery({
    queryKey: ["members", statusFilter, search],
    queryFn: () =>
      api<MembersList>(
        `/api/v1/members?${new URLSearchParams({
          ...(statusFilter !== "all" ? { status: statusFilter } : {}),
          ...(search ? { search } : {}),
          limit: "200",
        })}`,
      ),
    enabled: !!user,
  });

  if (authLoading || !user) {
    return (
      <AppShell>
        <div className="text-tertiary">Loading…</div>
      </AppShell>
    );
  }

  const counts = data?.counts_by_status ?? {};
  const chips: Array<[label: string, key: string]> = [
    ["All", "all"],
    ["Active", "active"],
    ["Frozen", "frozen"],
    ["Expired", "expired"],
    ["Inactive", "inactive"],
  ];

  const setStatus = (key: string) => {
    const q = new URLSearchParams(Array.from(params.entries()));
    if (key === "all") q.delete("status");
    else q.set("status", key);
    router.push(`/members${q.toString() ? `?${q}` : ""}`);
  };

  return (
    <AppShell>
      <PageHeader
        crumbs={["Operations", "Members"]}
        title="Members"
        accent={data ? `· ${data.total}` : ""}
        actions={
          <>
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Name, phone, email…"
              className="w-56 rounded-md border border-input bg-input-bg px-3 py-2 text-base text-primary placeholder:text-tertiary focus:border-coral focus:outline-none"
            />
            <Button icon={<IconFilter size={14} />}>Filter</Button>
            <Button variant="primary" icon={<IconPlus size={14} />}>
              Add member
            </Button>
          </>
        }
      />

      <div className="mb-4 flex flex-wrap gap-2">
        {chips.map(([label, key]) => {
          const active = statusFilter === key;
          const count = counts[key] ?? 0;
          return (
            <button
              key={key}
              type="button"
              onClick={() => setStatus(key)}
              className={[
                "flex items-center gap-1.5 rounded-sm border px-2.5 py-1 font-mono text-xs uppercase tracking-caps transition-colors",
                active
                  ? "border-strong bg-card text-primary"
                  : "border-subtle text-secondary hover:bg-elev hover:text-primary",
              ].join(" ")}
            >
              {label}
              <span className="text-tertiary">{count}</span>
            </button>
          );
        })}
      </div>

      <div className="overflow-hidden rounded-md border border-subtle bg-card">
        <table className="w-full text-md">
          <thead>
            <tr className="border-b border-subtle">
              <th className="px-4 py-2.5 text-left font-mono text-xs font-medium uppercase tracking-caps text-tertiary">
                Member
              </th>
              <th className="px-4 py-2.5 text-left font-mono text-xs font-medium uppercase tracking-caps text-tertiary">
                Status
              </th>
              <th className="px-4 py-2.5 text-left font-mono text-xs font-medium uppercase tracking-caps text-tertiary">
                Plan
              </th>
              <th className="px-4 py-2.5 text-left font-mono text-xs font-medium uppercase tracking-caps text-tertiary">
                Usage
              </th>
              <th className="px-4 py-2.5 text-left font-mono text-xs font-medium uppercase tracking-caps text-tertiary">
                Expires
              </th>
              <th className="w-12 px-4 py-2.5" />
            </tr>
          </thead>
          <tbody>
            {(data?.items ?? []).map((m) => {
              const pct =
                m.visit_limit && m.visits_remaining !== null
                  ? ((m.visit_limit - m.visits_remaining) / m.visit_limit) * 100
                  : null;
              const urgent = m.days_left !== null && m.days_left <= 3;
              return (
                <tr
                  key={m.id}
                  className="cursor-pointer border-b border-subtle last:border-0 hover:bg-elev"
                  onClick={() => router.push(`/members/${m.id}`)}
                >
                  <td className="px-4 py-3.5">
                    <div className="flex items-center gap-2.5">
                      <div
                        className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-gradient-to-br ${gradientFor(m.id)} text-xs font-semibold text-white`}
                      >
                        {m.initials}
                      </div>
                      <div>
                        <div className="font-medium text-primary">
                          {m.full_name}
                        </div>
                        <div className="font-mono text-sm text-tertiary">
                          {m.phone}
                        </div>
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-3.5">
                    <span className={pillClass(m.status)}>{m.status}</span>
                  </td>
                  <td className="px-4 py-3.5">
                    {m.plan_name ? (
                      <>
                        <div className="text-primary">{m.plan_name}</div>
                        <div className="font-mono text-sm text-tertiary">
                          {m.plan_type}
                        </div>
                      </>
                    ) : (
                      <span className="text-tertiary">—</span>
                    )}
                  </td>
                  <td className="px-4 py-3.5">
                    {m.visit_limit !== null && m.visits_remaining !== null ? (
                      <>
                        <div className="h-1 w-24 overflow-hidden rounded-sm bg-elev">
                          <div
                            className={`h-full ${
                              pct! > 70
                                ? "bg-danger"
                                : pct! > 40
                                ? "bg-warning"
                                : "bg-ozone"
                            }`}
                            style={{ width: `${pct}%` }}
                          />
                        </div>
                        <div className="mt-1 font-mono text-xs text-tertiary">
                          {m.visits_remaining} / {m.visit_limit} left
                        </div>
                      </>
                    ) : (
                      <span className="font-mono text-sm text-tertiary">∞</span>
                    )}
                  </td>
                  <td className="px-4 py-3.5">
                    {m.days_left !== null ? (
                      <span
                        className={`font-mono text-sm ${
                          urgent ? "text-danger" : "text-secondary"
                        }`}
                      >
                        {m.days_left > 0 ? `in ${m.days_left}d` : "expired"}
                      </span>
                    ) : (
                      <span className="text-tertiary">—</span>
                    )}
                  </td>
                  <td className="px-4 py-3.5 text-tertiary">
                    <Link
                      href={`/members/${m.id}`}
                      onClick={(e) => e.stopPropagation()}
                      className="font-mono text-md hover:text-primary"
                    >
                      →
                    </Link>
                  </td>
                </tr>
              );
            })}
            {data && data.items.length === 0 && (
              <tr>
                <td colSpan={6} className="px-4 py-16 text-center text-tertiary">
                  No members match these filters.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </AppShell>
  );
}

export default function MembersPage() {
  return (
    <Suspense
      fallback={
        <AppShell>
          <div className="text-tertiary">Loading…</div>
        </AppShell>
      }
    >
      <MembersPageInner />
    </Suspense>
  );
}
