export type ExpiringMember = {
  id: string;
  name: string;
  initials: string;
  plan: string;
  daysLeft: number;
  avatarGradient: string;
};

export function ExpiringList({ members }: { members: ExpiringMember[] }) {
  return (
    <ul role="list" className="divide-y divide-subtle">
      {members.map((m) => {
        const urgent = m.daysLeft <= 3;
        const warning = !urgent && m.daysLeft <= 7;
        return (
          <li key={m.id} className="flex items-center gap-3 py-2.5">
            <div
              className={[
                "flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-sm font-semibold text-white",
                m.avatarGradient,
              ].join(" ")}
            >
              {m.initials}
            </div>
            <div className="min-w-0 flex-1">
              <div className="truncate text-md font-medium text-primary">
                {m.name}
              </div>
              <div className="truncate font-mono text-sm text-tertiary">
                {m.plan}
              </div>
            </div>
            <div className="text-right">
              <div
                className={[
                  "text-xl font-semibold leading-none tabular-nums",
                  urgent
                    ? "text-danger"
                    : warning
                    ? "text-warning"
                    : "text-primary",
                ].join(" ")}
              >
                {m.daysLeft}
              </div>
              <div className="font-mono text-2xs uppercase tracking-caps text-tertiary">
                days left
              </div>
            </div>
          </li>
        );
      })}
      {members.length === 0 && (
        <li className="py-6 text-center text-tertiary">No upcoming expirations.</li>
      )}
    </ul>
  );
}
