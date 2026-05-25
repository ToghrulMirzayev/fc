export function Panel({
  title,
  tabs,
  action,
  children,
}: {
  title: string;
  tabs?: { label: string; active?: boolean }[];
  action?: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <section className="rounded-md border border-subtle bg-card p-5">
      <header className="mb-5 flex items-center justify-between">
        <h2 className="text-lg font-semibold tracking-tight text-primary">
          {title}
        </h2>
        {tabs && (
          <div className="flex gap-1 rounded-sm bg-elev p-0.5 font-mono text-xs">
            {tabs.map((t) => (
              <button
                key={t.label}
                type="button"
                className={[
                  "rounded-sm px-2.5 py-1 uppercase tracking-caps transition-colors",
                  t.active
                    ? "bg-card text-primary"
                    : "text-tertiary hover:text-secondary",
                ].join(" ")}
              >
                {t.label}
              </button>
            ))}
          </div>
        )}
        {action && <div>{action}</div>}
      </header>
      {children}
    </section>
  );
}
