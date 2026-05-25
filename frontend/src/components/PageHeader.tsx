"use client";

import { IconSearch } from "./icons";

/**
 * Page header used on every screen.
 *
 * Layout: breadcrumbs + heading on the left, actions on the right.
 *
 * The `accent` prop appends a muted phrase to the heading — useful for
 * "Members / 847" style or "Tuesday, good morning" greetings. Kept
 * understated (no italic, no extreme color) so it reads cleanly in
 * both light and dark themes.
 */
export function PageHeader({
  crumbs,
  title,
  accent,
  actions,
}: {
  crumbs: string[];
  title: string;
  accent?: string;
  actions?: React.ReactNode;
}) {
  return (
    <header className="mb-8 flex items-start justify-between gap-4">
      <div>
        <div className="font-mono text-xs uppercase tracking-caps text-tertiary">
          {crumbs.join(" / ")}
        </div>
        <h1 className="mt-1.5 text-3xl font-semibold tracking-tight text-primary">
          {title}
          {accent && (
            <span className="ml-2 font-normal text-tertiary">{accent}</span>
          )}
        </h1>
      </div>
      {actions && (
        <div className="flex shrink-0 items-center gap-2">{actions}</div>
      )}
    </header>
  );
}

export function SearchBox({
  placeholder = "Search members, plans, payments…",
}: {
  placeholder?: string;
}) {
  return (
    <div className="relative">
      <span className="pointer-events-none absolute left-2.5 top-1/2 -translate-y-1/2 text-tertiary">
        <IconSearch size={12} />
      </span>
      <input
        type="text"
        placeholder={placeholder}
        className="w-56 rounded-md border border-input bg-input-bg py-2 pl-8 pr-12 text-base text-primary placeholder:text-tertiary focus:border-coral focus:outline-none"
      />
      <span className="pointer-events-none absolute right-2.5 top-1/2 -translate-y-1/2 rounded-sm border border-subtle px-1.5 py-0.5 font-mono text-2xs text-dim">
        ⌘K
      </span>
    </div>
  );
}

export function Button({
  variant = "default",
  icon,
  children,
  onClick,
  type = "button",
  disabled = false,
}: {
  variant?: "default" | "primary";
  icon?: React.ReactNode;
  children: React.ReactNode;
  onClick?: () => void;
  type?: "button" | "submit";
  disabled?: boolean;
}) {
  const styles =
    variant === "primary"
      ? "bg-coral border-coral text-white hover:bg-coral-dim hover:border-coral-dim"
      : "bg-card border-subtle text-primary hover:bg-card-hover hover:border-strong";
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className={[
        "flex items-center gap-1.5 rounded-md border px-3.5 py-2 text-base font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-50",
        styles,
      ].join(" ")}
    >
      {icon}
      {children}
    </button>
  );
}
