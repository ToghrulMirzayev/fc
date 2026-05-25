import type { Config } from "tailwindcss";

/**
 * Fitness Court design tokens.
 *
 * Brand colors:
 *   accent  — warm orange (#FF5722), the plate color
 *   black/white — text and surfaces
 *
 * Tailwind utilities map to CSS variables defined in globals.css, so
 * light/dark themes swap the values and components stay theme-agnostic.
 *
 * Naming note: `coral` is kept as an alias of `accent` for backwards
 * compatibility — existing class names like `bg-coral-soft` still work
 * because the new orange occupies the same role coral did before.
 */
const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        ink: "var(--color-ink)",
        base: "var(--color-base)",
        elev: "var(--color-elev)",
        card: "var(--color-card)",
        "card-hover": "var(--color-card-hover)",

        primary: "var(--color-text-primary)",
        secondary: "var(--color-text-secondary)",
        tertiary: "var(--color-text-tertiary)",
        dim: "var(--color-text-dim)",

        // Brand accent
        accent: {
          DEFAULT: "var(--color-accent)",
          dim: "var(--color-accent-dim)",
        },
        // Backwards-compatible alias (was coral in the previous theme)
        coral: {
          DEFAULT: "var(--color-accent)",
          dim: "var(--color-accent-dim)",
        },

        ozone: {
          DEFAULT: "var(--color-ozone)",
          dim: "var(--color-ozone-dim)",
        },
        ice: "var(--color-ice)",
        warning: "var(--color-warning)",
        danger: "var(--color-danger)",
      },
      backgroundColor: {
        "accent-soft": "var(--color-accent-soft)",
        "coral-soft": "var(--color-accent-soft)",
        "ozone-soft": "var(--color-ozone-soft)",
        "ice-soft": "var(--color-ice-soft)",
        "danger-soft": "var(--color-danger-soft)",
        "warning-soft": "var(--color-warning-soft)",
        "input-bg": "var(--color-input-bg)",
      },
      borderColor: {
        subtle: "var(--color-border-subtle)",
        strong: "var(--color-border-strong)",
        input: "var(--color-input-border)",
      },
      fontFamily: {
        display: ["Inter", "-apple-system", "sans-serif"],
        sans: [
          "Inter",
          "-apple-system",
          "BlinkMacSystemFont",
          "Segoe UI",
          "sans-serif",
        ],
        mono: ["JetBrains Mono", "SF Mono", "Menlo", "monospace"],
      },
      fontSize: {
        "2xs": ["10px", { lineHeight: "1.4" }],
        xs: ["11px", { lineHeight: "1.4" }],
        sm: ["12px", { lineHeight: "1.4" }],
        base: ["13px", { lineHeight: "1.5" }],
        md: ["14px", { lineHeight: "1.5" }],
        lg: ["15px", { lineHeight: "1.5" }],
        xl: ["18px", { lineHeight: "1.3" }],
        "2xl": ["22px", { lineHeight: "1.2" }],
        "3xl": ["28px", { lineHeight: "1.15" }],
        "4xl": ["36px", { lineHeight: "1.1" }],
        "5xl": ["52px", { lineHeight: "1.05" }],
      },
      borderRadius: {
        sm: "6px",
        md: "10px",
        lg: "14px",
      },
      letterSpacing: {
        tighter: "-0.02em",
        tight: "-0.01em",
        caps: "0.06em",
        capsxl: "0.1em",
      },
      boxShadow: {
        frame: "0 24px 64px rgba(0, 0, 0, 0.4), 0 2px 8px rgba(0, 0, 0, 0.2)",
      },
    },
  },
  plugins: [],
};

export default config;
