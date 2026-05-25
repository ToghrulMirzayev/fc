/**
 * Attendance chart — area + line, with optional comparison series.
 *
 * Built as a hand-rolled SVG. We don't pull in Recharts or D3 for v1.0
 * because the chart is single-purpose and the bundle savings matter.
 * When we have 3+ chart types, switch to Recharts.
 *
 * `data` is the current period; `compare` is the previous period (dashed).
 * Both are arrays of numbers; the chart auto-scales to the max value.
 */
export function AttendanceChart({
  data,
  compare,
  yMax = 240,
  xLabels = ["Apr 16", "Apr 23", "Apr 30", "May 7", "May 14"],
}: {
  data: number[];
  compare?: number[];
  yMax?: number;
  xLabels?: string[];
}) {
  const W = 600;
  const H = 196;

  const toPoints = (values: number[]) =>
    values
      .map((v, i) => {
        const x = (i / (values.length - 1)) * W;
        const y = H - (v / yMax) * H;
        return `${x.toFixed(1)},${y.toFixed(1)}`;
      })
      .join(" ");

  const linePoints = toPoints(data);
  const areaPath = `M${linePoints
    .split(" ")
    .map((p) => `L${p}`)
    .join("")
    .slice(1)} L${W},${H} L0,${H} Z`;
  const comparePoints = compare ? toPoints(compare) : null;

  // Last point — get coords for the endpoint marker
  const lastX = W;
  const lastY = H - (data[data.length - 1] / yMax) * H;

  const yTicks = [yMax, yMax * 0.75, yMax * 0.5, yMax * 0.25, 0];

  return (
    <div className="relative h-56">
      {/* Y axis labels */}
      <div className="absolute bottom-6 left-0 top-0 flex w-8 flex-col justify-between font-mono text-2xs text-dim">
        {yTicks.map((t, i) => (
          <span key={i}>{Math.round(t)}</span>
        ))}
      </div>

      {/* Chart area */}
      <svg
        className="absolute bottom-6 left-9 right-0 top-0 h-[calc(100%-1.5rem)] w-[calc(100%-2.25rem)]"
        viewBox={`0 0 ${W} ${H}`}
        preserveAspectRatio="none"
        aria-label="Attendance chart"
        role="img"
      >
        <defs>
          <linearGradient id="chartGrad" x1="0" x2="0" y1="0" y2="1">
            <stop offset="0%" stopColor="var(--color-coral)" stopOpacity="0.18" />
            <stop offset="100%" stopColor="var(--color-coral)" stopOpacity="0" />
          </linearGradient>
        </defs>

        {/* Grid lines */}
        {[0.25, 0.5, 0.75].map((p) => (
          <line
            key={p}
            x1="0"
            y1={H * p}
            x2={W}
            y2={H * p}
            stroke="var(--color-border-subtle)"
            strokeWidth="1"
          />
        ))}

        {/* Area under primary line */}
        <path d={areaPath} fill="url(#chartGrad)" />

        {/* Comparison line (dashed) */}
        {comparePoints && (
          <polyline
            points={comparePoints}
            fill="none"
            stroke="var(--color-text-dim)"
            strokeWidth="1.2"
            strokeDasharray="3 3"
          />
        )}

        {/* Primary line */}
        <polyline
          points={linePoints}
          fill="none"
          stroke="var(--color-coral)"
          strokeWidth="2"
        />

        {/* End point */}
        <circle cx={lastX} cy={lastY} r="8" fill="var(--color-coral)" opacity="0.25" />
        <circle cx={lastX} cy={lastY} r="4" fill="var(--color-coral)" />
      </svg>

      {/* X axis labels */}
      <div className="absolute bottom-0 left-9 right-0 flex justify-between pt-1.5 font-mono text-2xs text-dim">
        {xLabels.map((l) => (
          <span key={l}>{l}</span>
        ))}
      </div>
    </div>
  );
}

/**
 * Legend below the chart — small color swatches and labels.
 */
export function ChartLegend() {
  return (
    <div className="mt-4 flex gap-4 font-mono text-sm text-tertiary">
      <span className="flex items-center gap-1.5">
        <span className="inline-block h-0.5 w-2 bg-coral" />
        This period
      </span>
      <span className="flex items-center gap-1.5">
        <span
          className="inline-block h-0.5 w-2"
          style={{ background: "var(--color-text-dim)" }}
        />
        Previous
      </span>
    </div>
  );
}
