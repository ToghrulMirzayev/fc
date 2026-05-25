/**
 * Branding strings — single source of truth for the product name on the frontend.
 *
 * To rebrand:
 * 1. Set NEXT_PUBLIC_APP_NAME in .env
 * 2. Edit copy below
 * 3. Replace artwork in components/Logo.tsx if you have new icon
 *
 * No string literal of the product name should appear anywhere else in the
 * frontend — always import from here.
 */

export const appName = (): string =>
  process.env.NEXT_PUBLIC_APP_NAME || "Fitness Court";

export const copy = {
  loginTitle: () => `Sign in to ${appName()}`,
  loginSubtitle: () => `Run your gym with ${appName()}`,
  appFullTitle: () => `${appName()} — Gym Management Platform`,
  copyright: () => `© ${new Date().getFullYear()} ${appName()}`,
} as const;
