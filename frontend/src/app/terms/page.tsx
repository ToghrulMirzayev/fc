"use client";

import Link from "next/link";
import { Logo } from "@/components/Logo";
import { ThemeToggle } from "@/components/ThemeToggle";
import { appName } from "@/lib/branding";

export default function TermsPage() {
  return (
    <div className="min-h-screen bg-ink flex flex-col">
      <header className="flex items-center justify-between border-b border-subtle px-8 py-5">
        <Logo size={32} />
        <div className="flex items-center gap-4">
          <ThemeToggle variant="compact" />
          <Link
            href="/signup"
            className="text-md font-medium text-secondary hover:text-coral"
          >
            ← Back to Sign Up
          </Link>
        </div>
      </header>

      <main className="flex-1 mx-auto max-w-3xl px-6 py-16">
        <article className="prose prose-invert">
          <h1 className="text-4xl font-semibold tracking-tight text-primary mb-2">
            Terms of Service
          </h1>
          <p className="text-sm text-tertiary mb-8">Last updated: July 11, 2026</p>

          <section className="space-y-6 text-secondary leading-relaxed">
            <p>
              Welcome to <strong>{appName()}</strong>. By requesting a workspace, signing up, or using our gym management software platform (the "Service"), you agree to be bound by these Terms of Service ("Terms").
            </p>

            <h2 className="text-xl font-semibold text-primary mt-8 mb-3">1. Description of Service</h2>
            <p>
              {appName()} provides gym owners and fitness studio managers with a web-based CRM and management system to track memberships, visits, billing, and connect with members via automated bots.
            </p>

            <h2 className="text-xl font-semibold text-primary mt-8 mb-3">2. User Accounts and Workspaces</h2>
            <ul className="list-disc pl-6 space-y-2">
              <li>You must provide accurate and complete information when requesting a workspace.</li>
              <li>You are responsible for safeguarding your login credentials and for all activities that occur under your workspace.</li>
              <li>We reserve the right to suspend or terminate workspaces that violate these Terms or are used for illegal or unauthorized activities.</li>
            </ul>

            <h2 className="text-xl font-semibold text-primary mt-8 mb-3">3. Acceptable Use</h2>
            <p>
              You agree not to misuse the Service or assist anyone else in doing so. This includes attempting to compromise the security, integrity, or availability of our servers or endpoints, or hosting data that violates third-party rights or local laws.
            </p>

            <h2 className="text-xl font-semibold text-primary mt-8 mb-3">4. Limitation of Liability</h2>
            <p>
              To the maximum extent permitted by law, the Service is provided "as is" and "as available." We make no warranties of any kind regarding reliability, accuracy, or uninterrupted availability. In no event shall {appName()} be liable for any indirect, incidental, or consequential damages.
            </p>

            <h2 className="text-xl font-semibold text-primary mt-8 mb-3">5. Changes to Terms</h2>
            <p>
              We may update these Terms from time to time. If we make material modifications, we will notify workspace owners. Continued use of the Service after changes become effective constitutes acceptance of the new Terms.
            </p>

            <h2 className="text-xl font-semibold text-primary mt-8 mb-3">6. Contact</h2>
            <p>
              If you have any questions about these Terms, please contact us at{" "}
              <a href="mailto:support@fitness-court.local" className="text-coral hover:underline">
                support@fitness-court.local
              </a>.
            </p>
          </section>
        </article>
      </main>
    </div>
  );
}
