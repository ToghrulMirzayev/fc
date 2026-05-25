"use client";

import { useQuery } from "@tanstack/react-query";

import { AppShell } from "@/components/AppShell";
import { AttendanceChart, ChartLegend } from "@/components/AttendanceChart";
import { ExpiringList, type ExpiringMember } from "@/components/ExpiringList";
import { IconDownload, IconPlus } from "@/components/icons";
import { KpiCard } from "@/components/KpiCard";
import { PageHeader, SearchBox, Button } from "@/components/PageHeader";
import { Panel } from "@/components/Panel";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/useAuth";

type DashboardData = {
  kpis: Array<{
    label: string;
    value: string;
    unit?: string;
    delta?: { direction: "up" | "down"; text: string };
    spark: number[];
  }>;
  attendance: {
    current: number[];
    previous: number[];
    y_max: number;
    x_labels: string[];
  };
  expiring: Array<{
    id: string;
    name: string;
    initials: string;
    plan: string;
    days_left: number;
    avatar_gradient: string;
  }>;
};

function greeting(): string {
  const h = new Date().getHours();
  if (h < 12) return "Good morning";
  if (h < 18) return "Good afternoon";
  return "Good evening";
}

export default function DashboardPage() {
  const { user, isLoading: authLoading } = useAuth();
  const { data, isLoading } = useQuery({
    queryKey: ["dashboard"],
    queryFn: () => api<DashboardData>("/api/v1/dashboard"),
    enabled: !!user,
  });

  if (authLoading || !user) {
    return (
      <AppShell>
        <div className="text-tertiary">Loading…</div>
      </AppShell>
    );
  }

  const firstName = user.full_name.split(" ")[0];

  const expiring: ExpiringMember[] = (data?.expiring ?? []).map((e) => ({
    id: e.id,
    name: e.name,
    initials: e.initials,
    plan: e.plan,
    daysLeft: e.days_left,
    avatarGradient: e.avatar_gradient,
  }));

  return (
    <AppShell>
      <PageHeader
        crumbs={["Operations", "Dashboard"]}
        title={`${greeting()}, ${firstName}.`}
        actions={
          <>
            <SearchBox />
            <Button icon={<IconDownload size={14} />}>Export</Button>
            <Button variant="primary" icon={<IconPlus size={14} />}>
              New member
            </Button>
          </>
        }
      />

      <div className="mb-8 grid grid-cols-4 gap-4">
        {(data?.kpis ?? Array(4).fill(null)).map((kpi, i) =>
          kpi ? (
            <KpiCard
              key={i}
              label={kpi.label}
              value={kpi.value}
              unit={kpi.unit}
              delta={kpi.delta}
              spark={kpi.spark}
            />
          ) : (
            <div
              key={i}
              className="h-32 animate-pulse rounded-md border border-subtle bg-card"
            />
          ),
        )}
      </div>

      <div className="grid gap-4" style={{ gridTemplateColumns: "1.6fr 1fr" }}>
        <Panel
          title="Daily attendance"
          tabs={[
            { label: "7d" },
            { label: "30d", active: true },
            { label: "90d" },
          ]}
        >
          {data ? (
            <>
              <AttendanceChart
                data={data.attendance.current}
                compare={data.attendance.previous}
                yMax={data.attendance.y_max}
                xLabels={data.attendance.x_labels}
              />
              <ChartLegend />
            </>
          ) : (
            <div className="h-56 animate-pulse rounded-md bg-elev" />
          )}
        </Panel>

        <Panel
          title="Expiring soon"
          action={
            <a
              href="/members?status=active"
              className="font-mono text-sm uppercase tracking-caps text-tertiary hover:text-coral"
            >
              View all →
            </a>
          }
        >
          {isLoading ? (
            <div className="space-y-2">
              {[1, 2, 3, 4].map((i) => (
                <div
                  key={i}
                  className="h-12 animate-pulse rounded-md bg-elev"
                />
              ))}
            </div>
          ) : (
            <ExpiringList members={expiring} />
          )}
        </Panel>
      </div>
    </AppShell>
  );
}
