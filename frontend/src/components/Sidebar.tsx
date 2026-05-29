"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { Logo } from "./Logo";
import { ThemeToggle } from "./ThemeToggle";
import {
  IconBookings,
  IconCheckins,
  IconDashboard,
  IconMembers,
  IconNotifications,
  IconPayments,
  IconPlans,
  IconSchedule,
  IconSettings,
} from "./icons";
import { useAuth } from "@/lib/useAuth";

type NavItem = {
  href: string;
  label: string;
  icon: (props: { size?: number }) => React.JSX.Element;
};

const NAV_GROUPS: Array<{ label: string; items: NavItem[] }> = [
  {
    label: "Operations",
    items: [
      { href: "/", label: "Dashboard", icon: IconDashboard },
      { href: "/members", label: "Members", icon: IconMembers },
      { href: "/checkins", label: "Check-ins", icon: IconCheckins },
      { href: "/bookings", label: "Bookings", icon: IconBookings },
    ],
  },
  {
    label: "Catalog",
    items: [
      { href: "/plans", label: "Plans", icon: IconPlans },
      { href: "/payments", label: "Payments", icon: IconPayments },
      { href: "/schedule", label: "Schedule", icon: IconSchedule },
    ],
  },
  {
    label: "Settings",
    items: [
      {
        href: "/notifications",
        label: "Notifications",
        icon: IconNotifications,
      },
      { href: "/configuration", label: "Configuration", icon: IconSettings },
    ],
  },
];

function initialsOf(name: string): string {
  const parts = name.trim().split(/\s+/);
  if (parts.length === 0) return "?";
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

export function Sidebar() {
  const pathname = usePathname();
  const { user } = useAuth();

  const isActive = (href: string) => {
    if (href === "/") return pathname === "/";
    return pathname === href || pathname.startsWith(`${href}/`);
  };

  return (
    <aside className="flex h-screen w-60 shrink-0 flex-col border-r border-subtle bg-base px-4 py-6">
      <div className="mb-4 flex items-center gap-2.5 border-b border-subtle px-2 pb-6">
        <Logo size={28} />
        {user?.tenant_slug && (
          <span className="ml-auto rounded-sm border border-subtle bg-elev px-1.5 py-0.5 font-mono text-2xs uppercase tracking-caps text-tertiary">
            {user.tenant_slug}
          </span>
        )}
      </div>

      <nav className="flex-1 overflow-y-auto">
        {NAV_GROUPS.map((group) => (
          <div key={group.label} className="mb-5">
            <div className="px-2 pb-2 font-mono text-xs uppercase tracking-capsxl text-dim">
              {group.label}
            </div>
            {group.items.map((item) => {
              const active = isActive(item.href);
              const Icon = item.icon;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={[
                    "relative flex items-center gap-2.5 rounded-sm px-2.5 py-2 text-md transition-colors",
                    active
                      ? "bg-coral-soft text-coral"
                      : "text-secondary hover:bg-elev hover:text-primary",
                  ].join(" ")}
                >
                  {active && (
                    <span
                      aria-hidden
                      className="absolute -left-4 top-2 bottom-2 w-0.5 rounded-r-sm bg-coral"
                    />
                  )}
                  <Icon size={16} />
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </div>
        ))}
      </nav>

      <div className="mt-auto space-y-2">
        <ThemeToggle />
        {user && (
          <Link
            href="/profile"
            className="flex w-full items-center gap-2.5 rounded-md border border-subtle bg-card p-2.5 text-left transition-colors hover:bg-card-hover"
          >
            <div
              className="flex h-7 w-7 items-center justify-center rounded-full text-2xs font-semibold text-white"
              style={{
                background:
                  "linear-gradient(135deg, var(--color-coral), var(--color-coral-dim))",
              }}
            >
              {initialsOf(user.full_name)}
            </div>
            <div className="min-w-0 flex-1">
              <div className="truncate text-base font-medium text-primary">
                {user.full_name}
              </div>
              <div className="font-mono text-xs text-tertiary">
                {user.role} · view profile
              </div>
            </div>
          </Link>
        )}
      </div>
    </aside>
  );
}
