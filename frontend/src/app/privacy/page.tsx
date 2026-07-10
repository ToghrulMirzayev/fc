"use client";

import Link from "next/link";
import { Logo } from "@/components/Logo";
import { ThemeToggle } from "@/components/ThemeToggle";
import { appName } from "@/lib/branding";

export default function PrivacyPage() {
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
            Privacy Policy
          </h1>
          <p className="text-sm text-tertiary mb-8">Last updated: July 11, 2026</p>

          <section className="space-y-6 text-secondary leading-relaxed">
            <p>
              At <strong>{appName()}</strong>, we value and respect your privacy. This Privacy Policy describes how we collect, use, and share information when you use our gym management software platform (the "Service").
            </p>

            <h2 className="text-xl font-semibold text-primary mt-8 mb-3">1. Information We Collect</h2>
            <p>
              We collect information to provide, maintain, and improve our Service. This includes:
            </p>
            <ul className="list-disc pl-6 space-y-2">
              <li>
                <strong>Account Information:</strong> When you request a workspace or sign up, we collect your name, email address, phone number, and details about your gym or company.
              </li>
              <li>
                <strong>Client/Member Data:</strong> To operate the CRM, our users (gym owners and staff) store membership details, check-in records, and billing details of their members.
              </li>
              <li>
                <strong>Usage and Server Logs:</strong> We log technical information automatically when you access the Service, including your IP address, browser type, and actions performed.
              </li>
            </ul>

            <h2 className="text-xl font-semibold text-primary mt-8 mb-3">2. How We Use Information</h2>
            <p>We use the collected information for the following purposes:</p>
            <ul className="list-disc pl-6 space-y-2">
              <li>To provision and manage your gym's tenant workspace.</li>
              <li>To facilitate check-ins and membership tracking.</li>
              <li>To maintain the security and stability of our servers (logs are used for system diagnostics and defense against attacks).</li>
              <li>To communicate with you regarding your service requests and updates.</li>
            </ul>

            <h2 className="text-xl font-semibold text-primary mt-8 mb-3">3. Data Retention and Deletion</h2>
            <p>
              We retain account data and customer logs for as long as necessary to fulfill the purposes outlined in this policy, or as required by law.
              You may request deletion of your account or tenant data at any time by contacting our support team. Upon verification, we will delete or anonymize your data within 30 days.
            </p>

            <h2 className="text-xl font-semibold text-primary mt-8 mb-3">4. Security and Tracking</h2>
            <p>
              We use standard technical measures (including HTTPS encryption) to secure all transmission of data.
              Currently, we do not use third-party analytics trackers, advertisement cookies, or pixel trackers.
            </p>

            <h2 className="text-xl font-semibold text-primary mt-8 mb-3">5. Contact Us</h2>
            <p>
              If you have any questions or concerns about this Privacy Policy or our data practices, please email us at{" "}
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
