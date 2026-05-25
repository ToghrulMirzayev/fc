import { AppShell } from "@/components/AppShell";
import { PageHeader } from "@/components/PageHeader";

/**
 * User-friendly placeholder for features still under construction.
 *
 * Internal: see ROADMAP.md for sprint scheduling. The user-facing copy
 * here intentionally avoids implementation details — we say what's
 * coming, not when. Roadmap commitments belong in private docs, not the
 * customer interface.
 */
export function ComingSoon({
  crumbs,
  title,
  headline,
  description,
}: {
  crumbs: string[];
  title: string;
  headline: string;
  description: string;
}) {
  return (
    <AppShell>
      <PageHeader crumbs={crumbs} title={title} />
      <div className="mt-12 flex justify-center">
        <div className="max-w-lg rounded-lg border border-subtle bg-card p-10 text-center">
          <div className="mx-auto mb-5 inline-flex h-12 w-12 items-center justify-center rounded-full bg-coral-soft">
            <span className="font-mono text-xs uppercase tracking-caps text-coral">
              Soon
            </span>
          </div>
          <h2 className="mb-3 text-2xl font-semibold tracking-tight text-primary">
            {headline}
          </h2>
          <p className="text-md text-secondary leading-relaxed">{description}</p>
          <p className="mt-6 text-sm text-tertiary">
            We're actively working on this — thanks for your patience.
          </p>
        </div>
      </div>
    </AppShell>
  );
}
