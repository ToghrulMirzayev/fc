import Link from "next/link";
import { appName } from "@/lib/branding";

export function Footer() {
  return (
    <footer className="w-full border-t border-subtle bg-ink py-6 mt-12">
      <div className="mx-auto max-w-6xl px-6 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="text-sm text-tertiary">
          © {new Date().getFullYear()} {appName()}. All rights reserved.
        </div>
        <div className="flex gap-6 text-sm text-secondary">
          <Link
            href="/privacy"
            className="hover:text-coral transition-colors underline decoration-subtle underline-offset-4"
          >
            Privacy Policy
          </Link>
          <Link
            href="/terms"
            className="hover:text-coral transition-colors underline decoration-subtle underline-offset-4"
          >
            Terms of Service
          </Link>
          <a
            href="mailto:support@fitness-court.local"
            className="hover:text-coral transition-colors underline decoration-subtle underline-offset-4"
          >
            Contact
          </a>
        </div>
      </div>
    </footer>
  );
}
