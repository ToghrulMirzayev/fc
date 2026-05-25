export function KpiCard({
  label,
  value,
  unit,
  delta,
  spark,
}: {
  label: string;
  value: string;
  unit?: string;
  delta?: { direction: "up" | "down"; text: string };
  spark?: number[];
}) {
  const sparkColor =
    delta?.direction === "down"
      ? "var(--color-danger)"
      : "var(--color-ozone)";

  return (
    <div className="relative overflow-hidden rounded-md border border-subtle bg-card p-5">
      <div className="mb-3 font-mono text-xs uppercase tracking-caps text-tertiary">
        {label}
      </div>
      <div className="mb-2 text-3xl font-semibold tracking-tight tabular-nums text-primary">
        {value}
        {unit && <span className="ml-0.5 text-lg text-tertiary">{unit}</span>}
      </div>
      {delta && (
        <span
          className={[
            "inline-flex items-center gap-1 rounded-sm px-1.5 py-0.5 font-mono text-xs font-medium",
            delta.direction === "up"
              ? "bg-ozone-soft text-ozone"
              : "bg-danger-soft text-danger",
          ].join(" ")}
        >
          {delta.direction === "up" ? "↗" : "↘"} {delta.text}
        </span>
      )}
      {spark && spark.length > 1 && (
        <svg
          className="absolute right-4 top-4"
          width={56}
          height={24}
          viewBox="0 0 56 24"
          aria-hidden
        >
          <polyline
            points={spark
              .map((v, i) => {
                const x = (i / (spark.length - 1)) * 56;
                const y = 24 - v * 20 - 2;
                return `${x.toFixed(1)},${y.toFixed(1)}`;
              })
              .join(" ")}
            fill="none"
            stroke={sparkColor}
            strokeWidth={1.5}
          />
        </svg>
      )}
    </div>
  );
}
