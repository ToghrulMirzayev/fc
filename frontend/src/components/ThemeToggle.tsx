"use client";

import { useTheme } from "@/lib/theme";

/**
 * Theme toggle in two layouts:
 * - default: full-width pill for the sidebar
 * - compact: square icon button for public headers
 */
export function ThemeToggle({
  variant = "default",
}: {
  variant?: "default" | "compact";
}) {
  const { theme, toggle } = useTheme();
  const isDark = theme === "dark";

  if (variant === "compact") {
    return (
      <button
        type="button"
        onClick={toggle}
        aria-label={`Switch to ${isDark ? "light" : "dark"} theme`}
        className="flex h-9 w-9 items-center justify-center rounded-md border border-subtle bg-card text-secondary transition-colors hover:bg-card-hover hover:text-primary"
      >
        {isDark ? <SunIcon /> : <MoonIcon />}
      </button>
    );
  }

  return (
    <button
      type="button"
      onClick={toggle}
      aria-label={`Switch to ${isDark ? "light" : "dark"} theme`}
      className="flex w-full items-center justify-between rounded-md border border-subtle bg-card px-3 py-2 text-tertiary transition-colors hover:bg-card-hover hover:text-primary"
    >
      <span className="font-mono text-2xs uppercase tracking-caps">
        {isDark ? "Dark" : "Light"} theme
      </span>
      <div className="flex items-center gap-1.5">
        <SunIcon dim={isDark} />
        <span className="h-3 w-px bg-subtle" />
        <MoonIcon dim={!isDark} />
      </div>
    </button>
  );
}

function SunIcon({ dim = false }: { dim?: boolean }) {
  return (
    <svg
      width={14}
      height={14}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={2}
      className={dim ? "opacity-40" : "text-coral"}
    >
      <circle cx="12" cy="12" r="4" />
      <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41" />
    </svg>
  );
}

function MoonIcon({ dim = false }: { dim?: boolean }) {
  return (
    <svg
      width={14}
      height={14}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={2}
      className={dim ? "opacity-40" : "text-coral"}
    >
      <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
    </svg>
  );
}
